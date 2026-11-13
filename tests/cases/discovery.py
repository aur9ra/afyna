# SPDX-License-Identifier: MPL-2.0

"""File discovery tests using temporary Linux directory trees."""

import errno
import os
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace

import pytest

from afyna import DiscoveryError, FileDiscoveryInventory, discover_files
from afyna import discovery


def test_records_are_compact():
    assert [field.name for field in fields(DiscoveryError)] == ["path", "error"]
    assert [field.name for field in fields(FileDiscoveryInventory)] == ["files", "errors"]


def test_nested_hidden_extensionless_sorted_and_nonregular(tmp_path):
    # ignore fifos and symlinks to them without reporting errors
    (tmp_path / ".hidden-dir").mkdir()
    (tmp_path / "empty").mkdir()
    names = [
        "z.flac",
        ".hidden",
        "README",
        ".hidden-dir/plain",
        "a.txt",
        "4°",
    ]
    for name in names:
        (tmp_path / name).touch()
    os.mkfifo(tmp_path / "fifo")
    (tmp_path / "fifo-link").symlink_to("fifo")
    inventory = discover_files(tmp_path)
    assert inventory.files == sorted((tmp_path / name for name in names), key=str)
    assert inventory.errors == []


def test_empty_source_directory_yields_nothing(tmp_path):
    inventory = discover_files(tmp_path)
    assert inventory.files == []
    assert inventory.errors == []


def test_sort_uses_lexical_pathname_spelling(tmp_path):
    # sort whole path strings, not individual components: "a.txt" < "a/nested"
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "nested").touch()
    (tmp_path / "a.txt").touch()
    inventory = discover_files(tmp_path)
    assert inventory.files == [tmp_path / "a.txt", tmp_path / "a" / "nested"]
    assert inventory.errors == []


@pytest.mark.parametrize("relative_root", [Path("."), Path("source"), Path("link/..")])
def test_relative_roots_are_rejected(relative_root):
    with pytest.raises(ValueError):
        discover_files(relative_root)


def test_preserves_symlink_and_meaningful_dotdot(tmp_path):
    # keep link/.. in the returned paths: it reaches target, not tmp_path
    (tmp_path / "target" / "child").mkdir(parents=True)
    (tmp_path / "target" / "found").touch()
    # collapsing link/.. to tmp_path would incorrectly include wrong
    (tmp_path / "wrong").touch()
    (tmp_path / "link").symlink_to("target/child", target_is_directory=True)
    root = tmp_path / "link" / ".."
    inventory = discover_files(root)
    assert inventory.files == [tmp_path / "link" / ".." / "found"]
    assert inventory.errors == []


def test_symlinked_root_outside_targets_and_independent_aliases(tmp_path):
    # follow each symlink path, even when several lead to the same directory
    # links may also lead outside the source directory
    source = tmp_path / "source"
    source.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "file").touch()
    (source / "local").mkdir()
    (source / "local" / "nested").touch()
    (source / "alias").symlink_to("local", target_is_directory=True)
    (source / "external").symlink_to(outside, target_is_directory=True)
    (source / "external-again").symlink_to(outside, target_is_directory=True)
    (source / "file-link").symlink_to(outside / "file")
    root = tmp_path / "root-link"
    root.symlink_to(source, target_is_directory=True)
    inventory = discover_files(root)
    expected_names = [
        "local/nested", "alias/nested", "external/file", "external-again/file", "file-link"
    ]
    assert inventory.files == sorted((root / name for name in expected_names), key=str)
    assert inventory.errors == []


def test_ancestor_cycles_are_silent(tmp_path):
    # skip links back to parent directories without errors; report broken
    # links and unresolvable symlink loops separately
    (tmp_path / "file").touch()
    (tmp_path / "child").mkdir()
    (tmp_path / "child" / "back").symlink_to("..", target_is_directory=True)
    (tmp_path / "self").symlink_to(".", target_is_directory=True)
    inventory = discover_files(tmp_path)
    assert inventory.files == [tmp_path / "file"]
    assert inventory.errors == []


@pytest.mark.parametrize("kind, expected_errno", [
    ("missing", errno.ENOENT), ("dangling", errno.ENOENT),
    ("file", errno.ENOTDIR), ("file-link", errno.ENOTDIR),
    ("loop", errno.ELOOP),
])
def test_invalid_roots_are_diagnostics(tmp_path, kind, expected_errno):
    root = tmp_path / "root"
    if kind == "file":
        root.touch()
    elif kind == "file-link":
        (tmp_path / "file").touch()
        root.symlink_to("file")
    elif kind == "dangling":
        root.symlink_to("missing")
    elif kind == "loop":
        root.symlink_to("root")
    inventory = discover_files(root)
    assert inventory.files == []
    assert len(inventory.errors) == 1
    assert inventory.errors[0].path == root
    assert inventory.errors[0].error.errno == expected_errno


def test_independent_link_failures_keep_successes(tmp_path):
    # keep files found elsewhere when a symlink cannot be resolved
    (tmp_path / "good").mkdir()
    (tmp_path / "good" / "file").touch()
    (tmp_path / "dangling").symlink_to("missing")
    (tmp_path / "loop-a").symlink_to("loop-b")
    (tmp_path / "loop-b").symlink_to("loop-a")
    inventory = discover_files(tmp_path)
    assert inventory.files == [tmp_path / "good" / "file"]
    assert {item.path.name: item.error.errno for item in inventory.errors} == {
        "dangling": errno.ENOENT, "loop-a": errno.ELOOP, "loop-b": errno.ELOOP,
    }


@pytest.mark.parametrize("operation", ["stat", "scandir"])
@pytest.mark.parametrize("at_root", [False, True])
def test_inaccessible_operations_retain_original_errors(tmp_path, monkeypatch, operation, at_root):
    # inject a permission error only at the blocked path and check that the
    # inventory retains the same exception object
    blocked = tmp_path if at_root else tmp_path / "blocked"
    if not at_root:
        blocked.mkdir()
    (blocked / "unseen").touch()
    (tmp_path / "good").touch()
    failure = PermissionError(errno.EACCES, "injected denial", str(blocked))
    original = getattr(discovery.os, operation)

    def fail_blocked(path, *args, **kwargs):
        if path == blocked:
            raise failure
        return original(path, *args, **kwargs)

    monkeypatch.setattr(discovery.os, operation, fail_blocked)
    inventory = discover_files(tmp_path)
    assert inventory.files == ([] if at_root else [tmp_path / "good"])
    assert len(inventory.errors) == 1
    assert inventory.errors[0].path == blocked
    assert inventory.errors[0].error is failure


@pytest.mark.parametrize("at_root, missing_field, unavailable", [
    (True, "st_dev", None),
    (False, "st_ino", None),
    (False, "st_ino", 0),
])
def test_unavailable_identity_prevents_descent(tmp_path, monkeypatch, at_root, missing_field, unavailable):
    # device and inode numbers are needed to detect directory loops
    # report an error and skip this directory if either is unavailable
    blocked = tmp_path if at_root else tmp_path / "blocked"
    if not at_root:
        blocked.mkdir()
    (blocked / "unseen").touch()
    (tmp_path / "good").touch()
    original_stat = discovery.os.stat
    original_scandir = discovery.os.scandir

    def unavailable_stat(path, *args, **kwargs):
        result = original_stat(path, *args, **kwargs)
        if path == blocked:
            values = {name: getattr(result, name) for name in ["st_mode", "st_dev", "st_ino"]}
            values[missing_field] = unavailable
            return SimpleNamespace(**values)
        return result

    def guarded_scandir(path):
        assert path != blocked, "must not enumerate without cycle protection"
        return original_scandir(path)

    monkeypatch.setattr(discovery.os, "stat", unavailable_stat)
    monkeypatch.setattr(discovery.os, "scandir", guarded_scandir)
    inventory = discover_files(tmp_path)
    assert inventory.files == ([] if at_root else [tmp_path / "good"])
    assert len(inventory.errors) == 1
    assert inventory.errors[0].path == blocked
    assert isinstance(inventory.errors[0].error, OSError)


def test_partial_enumeration_retains_observations_and_pending_child(tmp_path, monkeypatch):
    # fail after yielding entries; still process those entries, including
    # their subdirectories, and retain the error
    (tmp_path / "observed").touch()
    (tmp_path / "pending").mkdir()
    (tmp_path / "pending" / "file").touch()
    (tmp_path / "independent").mkdir()
    (tmp_path / "independent" / "file").touch()
    original = discovery.os.scandir
    failure = OSError(errno.EIO, "enumeration failed", str(tmp_path))

    class PartialEnumeration:
        def __enter__(self):
            return self.entries()

        def __exit__(self, *exception):
            return False

        def entries(self):
            for name in ["observed", "pending", "independent"]:
                yield SimpleNamespace(name=name)
            raise failure

    def partial_scandir(path):
        return PartialEnumeration() if path == tmp_path else original(path)

    monkeypatch.setattr(discovery.os, "scandir", partial_scandir)
    inventory = discover_files(tmp_path)
    expected_names = ["observed", "pending/file", "independent/file"]
    assert inventory.files == sorted((tmp_path / name for name in expected_names), key=str)
    assert len(inventory.errors) == 1
    assert inventory.errors[0].path == tmp_path
    assert inventory.errors[0].error is failure


@pytest.mark.parametrize("operation, exception_type", [
    ("stat", RuntimeError),
    ("scandir", RuntimeError),
    ("stat", KeyboardInterrupt),
    ("scandir", SystemExit),
])
def test_nonfilesystem_exceptions_propagate(tmp_path, monkeypatch, operation, exception_type):
    # only OSError is collected; other exceptions and interrupts propagate
    # scope the shared os patch to this call so pytest can use os afterward
    failure = exception_type("injected")

    def fail(*args, **kwargs):
        raise failure

    with monkeypatch.context() as patch:
        patch.setattr(discovery.os, operation, fail)
        with pytest.raises(exception_type) as caught:
            discover_files(tmp_path)
    assert caught.value is failure
