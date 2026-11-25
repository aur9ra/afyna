# SPDX-License-Identifier: MPL-2.0

"""Collection-level metadata observation inventory tests."""

import errno
import os
import shutil
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import NoReturn
from unittest.mock import Mock

import pytest

from afyna import (
    AudioFileMetadataEntry,
    AudioFileObservation,
    AudioFileObservationFailure,
    DiscoveryError,
    FileDiscoveryInventory,
    observe_flac_metadata,
    observe_metadata_inventory,
)
from tests.support.flac_bytes import vorbis_payload, write_flac

FIXTURE_AUDIO = Path(__file__).resolve().parents[1] / "fixtures" / "audio"


def _success(path):
    """Build a synthetic success with the filename as its title."""
    return AudioFileObservation(
        path, (AudioFileMetadataEntry("EXAMPLE TEST TITLE", path.name),)
    )


def _failure(path, error=None):
    """Build a failure with a supplied error."""
    if error is None:
        error = OSError(errno.EIO, "injected observation failure", str(path))
    return AudioFileObservationFailure(path, error)


def _unexpected_observation(path: Path) -> NoReturn:
    """Fail immediately if an unattempted path is passed to the observer."""
    raise AssertionError(f"unexpected observation of {path}")


def test_coverage_records_success_failure_and_unattempted(tmp_path):
    """Account for each supplied occurrence in order and leave discovery intact.

    Keep returned outcomes intact and discovery diagnostics separate from
    observation failures; skipped paths still occupy a slot in the inventory.
    """

    success_path = tmp_path / "ok.FLAC"
    unattempted_path = tmp_path / "notes.txt"
    failure_path = tmp_path / "bad.flac"
    blocked_path = tmp_path / "blocked"
    diagnostic_error = PermissionError(
        errno.EACCES, "injected denial", str(blocked_path)
    )

    success = _success(success_path)
    failure = _failure(failure_path)
    calls = []

    # isolate inventory bookkeeping from file contents and parser behavior
    def fake_observer(path: Path):
        calls.append(path)
        return success if path == success_path else failure

    discovery_inventory = FileDiscoveryInventory(
        files=[success_path, unattempted_path, failure_path],
        errors=[DiscoveryError(blocked_path, diagnostic_error)],
    )
    original_files = list(discovery_inventory.files)
    original_errors = list(discovery_inventory.errors)

    inventory = observe_metadata_inventory(
        discovery_inventory, flac_observer=fake_observer
    )

    assert calls == [success_path, failure_path]
    assert [occurrence.path for occurrence in inventory.occurrences] == [
        success_path,
        unattempted_path,
        failure_path,
    ]
    assert inventory.occurrences[0].outcome is success
    assert inventory.occurrences[1].outcome is None
    assert inventory.occurrences[2].outcome is failure
    assert len(inventory.discovery_errors) == 1
    assert inventory.discovery_errors[0].path == blocked_path
    assert inventory.discovery_errors[0].error is diagnostic_error
    assert discovery_inventory.files == original_files
    assert discovery_inventory.errors == original_errors


def test_none_observer_result_is_not_unattempted(tmp_path):
    """Reject None from an attempted observation rather than recording a skip."""

    path = tmp_path / "attempted.flac"
    observer = Mock(return_value=None)

    with pytest.raises(TypeError, match="flac_observer must not return None"):
        observe_metadata_inventory(
            FileDiscoveryInventory(files=[path]), flac_observer=observer
        )

    observer.assert_called_once_with(path)


def test_empty_discovery_produces_empty_inventory():
    """Return no occurrences or diagnostics and make no observer calls."""

    inventory = observe_metadata_inventory(
        FileDiscoveryInventory(), flac_observer=_unexpected_observation
    )

    assert inventory.occurrences == ()
    assert inventory.discovery_errors == ()


def test_diagnostic_only_discovery_retains_errors(tmp_path):
    """Keep the diagnostic path and original error without observing it."""

    blocked_path = tmp_path / "blocked"
    failure = PermissionError(errno.EACCES, "injected denial", str(blocked_path))
    inventory = observe_metadata_inventory(
        FileDiscoveryInventory(errors=[DiscoveryError(blocked_path, failure)]),
        flac_observer=_unexpected_observation,
    )

    assert inventory.occurrences == ()
    assert len(inventory.discovery_errors) == 1
    assert inventory.discovery_errors[0].path == blocked_path
    assert inventory.discovery_errors[0].error is failure


def test_baseline_and_diagnostics_are_independent_of_caller_mutation(tmp_path):
    """Capture file order and diagnostic bindings before the first observation.

    Edits during observation and after return must not alter the retained
    paths or replace the original diagnostic exception.
    """

    first = tmp_path / "first.flac"
    second = tmp_path / "second.FLAC"
    third = tmp_path / "third.FlAc"
    original_diagnostic_path = tmp_path / "blocked"
    original_error = PermissionError(
        errno.EACCES, "injected denial", str(original_diagnostic_path)
    )
    rebound_error = OSError(errno.EIO, "rebound failure")
    source_error = DiscoveryError(original_diagnostic_path, original_error)
    discovery_inventory = FileDiscoveryInventory(
        files=[first, second, third], errors=[source_error]
    )

    calls = []

    def fake_observer(path: Path):
        calls.append(path)
        if len(calls) == 1:
            # change both lists at the first call to detect deferred capture
            discovery_inventory.files.clear()
            discovery_inventory.files.append(tmp_path / "injected.flac")
            discovery_inventory.errors.clear()
            discovery_inventory.errors.append(
                DiscoveryError(tmp_path / "later", rebound_error)
            )
            # rebind fields on the diagnostic that a list copy would still share
            source_error.path = tmp_path / "rebound"
            source_error.error = rebound_error
        return _success(path)

    inventory = observe_metadata_inventory(
        discovery_inventory, flac_observer=fake_observer
    )

    assert calls == [first, second, third]
    assert [occurrence.path for occurrence in inventory.occurrences] == [
        first,
        second,
        third,
    ]
    assert inventory.discovery_errors[0].path == original_diagnostic_path
    assert inventory.discovery_errors[0].error is original_error

    discovery_inventory.files.append(tmp_path / "after.flac")
    source_error.path = tmp_path / "after"
    source_error.error = OSError(errno.EIO, "after return")

    assert [occurrence.path for occurrence in inventory.occurrences] == [
        first,
        second,
        third,
    ]
    assert inventory.discovery_errors[0].path == original_diagnostic_path
    assert inventory.discovery_errors[0].error is original_error


def test_returned_structures_reject_ordinary_mutation(tmp_path):
    """Require tuple collections and frozen field bindings.

    This checks structural stability, not deep immutability: the original
    outcome and discovery exception are retained by identity.
    """

    path = tmp_path / "song.flac"
    blocked_path = tmp_path / "blocked"
    discovery_failure = PermissionError(
        errno.EACCES, "injected denial", str(blocked_path)
    )
    observation_failure = _failure(path)

    inventory = observe_metadata_inventory(
        FileDiscoveryInventory(
            files=[path], errors=[DiscoveryError(blocked_path, discovery_failure)]
        ),
        flac_observer=lambda observed_path: observation_failure,
    )

    assert isinstance(inventory.occurrences, tuple)
    assert isinstance(inventory.discovery_errors, tuple)

    # use setattr to test invalid writes at runtime without Pyright diagnostics
    with pytest.raises(FrozenInstanceError):
        setattr(inventory, "occurrences", ())
    with pytest.raises(FrozenInstanceError):
        setattr(inventory, "discovery_errors", ())
    with pytest.raises(FrozenInstanceError):
        setattr(inventory.occurrences[0], "path", blocked_path)
    with pytest.raises(FrozenInstanceError):
        setattr(inventory.occurrences[0], "outcome", None)
    with pytest.raises(FrozenInstanceError):
        setattr(inventory.discovery_errors[0], "path", path)
    with pytest.raises(FrozenInstanceError):
        setattr(inventory.discovery_errors[0], "error", discovery_failure)

    retained_outcome = inventory.occurrences[0].outcome
    assert inventory.discovery_errors[0].error is discovery_failure
    assert retained_outcome is observation_failure
    assert isinstance(retained_outcome, AudioFileObservationFailure)
    assert retained_outcome.error is observation_failure.error


def test_returned_failure_does_not_prevent_later_observations(tmp_path):
    """Keep a returned failure in place and still observe later occurrences."""

    first = tmp_path / "first.flac"
    second = tmp_path / "second.flac"
    third = tmp_path / "third.flac"
    first_failure = _failure(first)
    second_success = _success(second)
    third_failure = _failure(third)
    outcomes = {
        first: first_failure,
        second: second_success,
        third: third_failure,
    }
    calls = []

    def fake_observer(path: Path):
        calls.append(path)
        return outcomes[path]

    inventory = observe_metadata_inventory(
        FileDiscoveryInventory(files=[first, second, third]),
        flac_observer=fake_observer,
    )

    assert calls == [first, second, third]
    assert inventory.occurrences[0].outcome is first_failure
    assert inventory.occurrences[1].outcome is second_success
    assert inventory.occurrences[2].outcome is third_failure


@pytest.mark.parametrize("exception_type", [RuntimeError, KeyboardInterrupt])
def test_unexpected_exceptions_and_interrupts_propagate(tmp_path, exception_type):
    """Propagate a raised error or interrupt unchanged and stop observing."""

    first = tmp_path / "first.flac"
    second = tmp_path / "second.flac"
    failure = exception_type("injected")
    calls = []

    def fake_observer(path: Path):
        calls.append(path)
        raise failure

    with pytest.raises(exception_type) as caught:
        observe_metadata_inventory(
            FileDiscoveryInventory(files=[first, second]), flac_observer=fake_observer
        )

    assert caught.value is failure
    assert calls == [first]


def test_preserves_aliases_and_repeated_occurrences(tmp_path):
    """Keep alias spellings, noncanonical paths, and exact repeats in order."""

    target_directory = tmp_path / "target"
    target_directory.mkdir()
    target_file = target_directory / "real.flac"
    target_file.touch()

    alias_a = tmp_path / "alias-a.flac"
    alias_b = tmp_path / "alias-b.flac"
    alias_a.symlink_to(target_file)
    alias_b.symlink_to(target_file)

    alias_directory = tmp_path / "alias-dir"
    alias_directory.mkdir()
    noncanonical = alias_directory / ".." / "target" / "real.flac"

    repeated = tmp_path / "repeat.flac"
    baseline = [alias_a, alias_b, noncanonical, repeated, repeated]
    # different outcomes for the same pathname expose reuse or deduplication
    outcomes = [
        _success(alias_a),
        _success(alias_b),
        _success(noncanonical),
        _success(repeated),
        _failure(repeated),
    ]
    calls = []

    def fake_observer(path: Path):
        calls.append(path)
        return outcomes[len(calls) - 1]

    inventory = observe_metadata_inventory(
        FileDiscoveryInventory(files=baseline), flac_observer=fake_observer
    )

    assert os.path.samefile(alias_a, alias_b)
    assert os.path.samefile(noncanonical, target_file)
    assert calls == baseline
    assert [occurrence.path for occurrence in inventory.occurrences] == baseline
    assert len(inventory.occurrences) == 5
    for occurrence, outcome in zip(inventory.occurrences, outcomes):
        assert occurrence.outcome is outcome


def test_routing_uses_observed_suffix_without_resolving(tmp_path):
    """Select by the case-insensitive suffix of the observed path.

    Pass selected Path objects unchanged. Selection is independent of the
    resolved target's suffix and does not imply that the content will parse.
    """

    differently_suffixed_target = tmp_path / "payload.bin"
    suffixed_target = tmp_path / "actual.flac"
    shutil.copyfile(FIXTURE_AUDIO / "minuet.flac", differently_suffixed_target)
    shutil.copyfile(FIXTURE_AUDIO / "minuet.flac", suffixed_target)

    lower = tmp_path / "lower.flac"
    upper = tmp_path / "upper.FLAC"
    mixed = tmp_path / "mixed.FlAc"
    # mismatched aliases catch both false positives and false negatives if
    # routing uses the target's suffix instead of the observed suffix
    flac_alias = tmp_path / "alias.flac"
    nonflac_alias = tmp_path / "alias.m4a"
    dot_flac = tmp_path / ".flac"
    for path in (lower, upper, mixed, nonflac_alias, dot_flac):
        path.symlink_to(suffixed_target)
    flac_alias.symlink_to(differently_suffixed_target)

    invalid = tmp_path / "invalid.flac"
    invalid.write_bytes(b"not a FLAC file")

    # both skipped names lead to readable FLAC; the dotfile has no Path.suffix
    assert isinstance(observe_flac_metadata(nonflac_alias), AudioFileObservation)
    assert isinstance(observe_flac_metadata(dot_flac), AudioFileObservation)

    calls = []

    def recording_observer(path: Path):
        calls.append(path)
        return observe_flac_metadata(path)

    inventory = observe_metadata_inventory(
        FileDiscoveryInventory(
            files=[
                lower,
                upper,
                mixed,
                flac_alias,
                nonflac_alias,
                dot_flac,
                invalid,
            ]
        ),
        flac_observer=recording_observer,
    )

    selected = [lower, upper, mixed, flac_alias, invalid]
    assert calls == selected
    assert all(called is expected for called, expected in zip(calls, selected))
    assert nonflac_alias not in calls
    assert dot_flac not in calls
    for occurrence in inventory.occurrences[:4]:
        assert isinstance(occurrence.outcome, AudioFileObservation)
        assert occurrence.outcome.metadata_entries is not None
    assert inventory.occurrences[4].outcome is None
    assert inventory.occurrences[5].outcome is None
    assert isinstance(inventory.occurrences[6].outcome, AudioFileObservationFailure)


def test_real_observer_preserves_fixture_evidence_and_empty_distinction(
    tmp_path,
):
    """Match direct fixture observation and preserve the copy's bytes.

    A missing Vorbis comment block and a present block with zero entries are
    distinct successful observations, not skipped paths or failures.
    """

    copied = tmp_path / "song.flac"
    shutil.copyfile(FIXTURE_AUDIO / "blackbird.flac", copied)
    before_bytes = copied.read_bytes()
    direct_observation = observe_flac_metadata(copied)
    assert isinstance(direct_observation, AudioFileObservation)

    # omit the block in one file and encode an empty entry list in the other
    absent = write_flac(tmp_path / "absent.flac")
    empty = write_flac(tmp_path / "empty.flac", vorbis_payload(()))

    inventory = observe_metadata_inventory(
        FileDiscoveryInventory(files=[copied, absent, empty])
    )
    outcomes = {
        occurrence.path: occurrence.outcome for occurrence in inventory.occurrences
    }

    copied_outcome = outcomes[copied]
    absent_outcome = outcomes[absent]
    empty_outcome = outcomes[empty]

    assert isinstance(copied_outcome, AudioFileObservation)
    assert isinstance(absent_outcome, AudioFileObservation)
    assert isinstance(empty_outcome, AudioFileObservation)

    assert copied_outcome == direct_observation
    assert copied_outcome.metadata_entries is not None
    assert absent_outcome.metadata_entries is None
    assert empty_outcome.metadata_entries == ()
    assert copied.read_bytes() == before_bytes


def test_inventory_remains_unchanged_after_source_changes(tmp_path):
    """Keep the same occurrence tuple and outcome as historical evidence."""

    path = tmp_path / "song.flac"
    shutil.copyfile(FIXTURE_AUDIO / "flamenco-road.flac", path)

    inventory = observe_metadata_inventory(FileDiscoveryInventory(files=[path]))
    original_occurrences = inventory.occurrences
    expected_outcome = inventory.occurrences[0].outcome
    assert isinstance(expected_outcome, AudioFileObservation)

    # invalidate the FLAC content while leaving its pathname in place
    path.write_bytes(b"changed after observation")
    assert inventory.occurrences is original_occurrences
    assert inventory.occurrences[0].outcome is expected_outcome

    path.unlink()
    assert inventory.occurrences is original_occurrences
    assert [occurrence.path for occurrence in inventory.occurrences] == [path]
    assert inventory.occurrences[0].outcome is expected_outcome


def test_observation_is_read_only_for_successes_and_failures(tmp_path):
    """Check file bytes, directory entries, and link text after observation.

    The checks cover successful and failed observations, not filesystem
    access times, which reads can update.
    """

    good = tmp_path / "good.flac"
    shutil.copyfile(FIXTURE_AUDIO / "minuet.flac", good)
    bad = tmp_path / "bad.flac"
    bad.write_bytes(b"not a FLAC file")
    alias = tmp_path / "alias.flac"
    alias.symlink_to(good)

    before_bytes = {
        good: good.read_bytes(),
        bad: bad.read_bytes(),
    }
    before_entries = sorted(os.listdir(tmp_path))
    before_link_target = os.readlink(alias)

    inventory = observe_metadata_inventory(
        FileDiscoveryInventory(files=[good, bad, alias])
    )

    assert isinstance(inventory.occurrences[0].outcome, AudioFileObservation)
    assert isinstance(inventory.occurrences[1].outcome, AudioFileObservationFailure)
    assert isinstance(inventory.occurrences[2].outcome, AudioFileObservation)
    assert good.read_bytes() == before_bytes[good]
    assert bad.read_bytes() == before_bytes[bad]
    assert sorted(os.listdir(tmp_path)) == before_entries
    assert os.readlink(alias) == before_link_target


def test_consumes_only_the_supplied_baseline(tmp_path):
    """Use only supplied occurrences rather than discovering nearby files."""

    supplied = tmp_path / "supplied.flac"
    undiscovered = tmp_path / "undiscovered.flac"
    undiscovered.touch()

    calls = []

    # use a stub so the supplied path need not exist to test baseline selection
    def fake_observer(path: Path):
        calls.append(path)
        return _success(path)

    inventory = observe_metadata_inventory(
        FileDiscoveryInventory(files=[supplied]), flac_observer=fake_observer
    )

    assert calls == [supplied]
    assert [occurrence.path for occurrence in inventory.occurrences] == [supplied]
