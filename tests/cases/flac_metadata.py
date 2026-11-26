# SPDX-License-Identifier: MPL-2.0

"""Read-only FLAC metadata observation tests."""

import errno
import os
import shutil
import threading
from pathlib import Path

import pytest
from mutagen import MutagenError

from afyna import (
    AudioFileMetadataEntry,
    AudioFileObservation,
    AudioFileObservationFailure,
    observe_flac_metadata,
)
from afyna.audio.file_formats.flac import metadata as flac_metadata
from afyna.audio.metadata_formats.vorbis_comment.parsing import (
    _IncompleteObservationError,
)
from tests.support.flac_bytes import vorbis_payload, write_flac

FIXTURE_AUDIO = Path(__file__).resolve().parents[1] / "fixtures" / "audio"

CANONICAL_ENTRIES = {
    "22sq.flac": (
        AudioFileMetadataEntry("ALBUM", "Fixture Album Two"),
        AudioFileMetadataEntry("ALBUMARTIST", "Fixture Artist Two"),
        AudioFileMetadataEntry("ARTIST", "Fixture Artist Two"),
        AudioFileMetadataEntry("TITLE", "22SQ"),
        AudioFileMetadataEntry("TRACKNUMBER", "2"),
    ),
    "black-cat-begging.flac": (
        AudioFileMetadataEntry("ALBUM", "Fixture Album Three"),
        AudioFileMetadataEntry("ALBUMARTIST", "Fixture Artist Three"),
        AudioFileMetadataEntry("ARTIST", "Fixture Artist Three"),
        AudioFileMetadataEntry("TITLE", "Black cat sound begging the foods"),
        AudioFileMetadataEntry("TRACKNUMBER", "1"),
    ),
    "blackbird.flac": (
        AudioFileMetadataEntry("ALBUM", "Fixture Album One"),
        AudioFileMetadataEntry("ALBUMARTIST", "Fixture Artist One"),
        AudioFileMetadataEntry("ARTIST", "Fixture Artist One"),
        AudioFileMetadataEntry("TITLE", "Blackbird"),
        AudioFileMetadataEntry("TRACKNUMBER", "2"),
    ),
    "flamenco-road.flac": (
        AudioFileMetadataEntry("ALBUM", "Fixture Album One"),
        AudioFileMetadataEntry("ALBUMARTIST", "Fixture Artist One"),
        AudioFileMetadataEntry("ARTIST", "Fixture Artist One"),
        AudioFileMetadataEntry("TITLE", "Flamenco Road"),
        AudioFileMetadataEntry("TRACKNUMBER", "1"),
    ),
    "flanger-distorted-bass.flac": (
        AudioFileMetadataEntry("ALBUM", "Fixture Album Four"),
        AudioFileMetadataEntry("ALBUMARTIST", "Fixture Artist Four"),
        AudioFileMetadataEntry("ARTIST", "Fixture Artist Four"),
        AudioFileMetadataEntry("TITLE", "Fixture Title Four"),
        AudioFileMetadataEntry("TRACKNUMBER", "1"),
    ),
    "hans-im-schnokeloch.flac": (
        AudioFileMetadataEntry("ALBUM", "Fixture Album Two"),
        AudioFileMetadataEntry("ALBUMARTIST", "Fixture Artist Two"),
        AudioFileMetadataEntry("ARTIST", "Fixture Artist Two"),
        AudioFileMetadataEntry("TITLE", "D'r Hans im Schnokeloch"),
        AudioFileMetadataEntry("TRACKNUMBER", "1"),
    ),
    "ietf-cellar-subset-47.flac": (
        AudioFileMetadataEntry("ALBUM", "Fixture Album Six"),
        AudioFileMetadataEntry("ALBUMARTIST", "Fixture Artist Six"),
        AudioFileMetadataEntry("ARTIST", "Fixture Artist Six"),
        AudioFileMetadataEntry("TITLE", "Fixture Title Six"),
        AudioFileMetadataEntry("TRACKNUMBER", "1"),
    ),
    "minuet.flac": (
        AudioFileMetadataEntry("ALBUM", "Fixture Album One"),
        AudioFileMetadataEntry("ALBUMARTIST", "Fixture Artist One"),
        AudioFileMetadataEntry("ARTIST", "Fixture Artist One"),
        AudioFileMetadataEntry("TITLE", "Minuet in G Major"),
        AudioFileMetadataEntry("TRACKNUMBER", "3"),
    ),
    "unfa-braam.flac": (
        AudioFileMetadataEntry("ALBUM", "Fixture Album Five"),
        AudioFileMetadataEntry("ALBUMARTIST", "Fixture Artist Five"),
        AudioFileMetadataEntry("ARTIST", "Fixture Artist Five"),
        AudioFileMetadataEntry("TITLE", "Fixture Title Five"),
        AudioFileMetadataEntry("TRACKNUMBER", "1"),
    ),
}


def _entry(name, value):
    return f"{name}={value}".encode("utf-8")


def _observe_with_timeout(path, timeout=2.0):
    results = []

    def run():
        try:
            results.append(observe_flac_metadata(path))
        except BaseException as error:
            results.append(error)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(timeout)
    assert not thread.is_alive(), f"observation blocked for {timeout} seconds"
    assert results, "observation did not return a result"
    return results[0]


@pytest.mark.parametrize("filename, expected", CANONICAL_ENTRIES.items())
def test_canonical_fixtures_preserve_known_metadata(filename, expected):
    path = FIXTURE_AUDIO / filename
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservation), result
    assert result.path == path
    assert result.metadata_entries == expected


def test_preserves_spelling_order_duplicates_conflicts_and_whitespace(tmp_path):
    payload = vorbis_payload(
        [
            b"title=First",
            b"ALBUM=Same",
            b"ALBUM=Different",
            b"ALBUM=Same",
            b"EMPTY=",
            _entry("ARTIST", "Björk"),
            b" TITLE =  padded value  ",
        ]
    )
    path = write_flac(tmp_path / "tags.flac", payload)
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservation), result
    assert result.metadata_entries == (
        AudioFileMetadataEntry("title", "First"),
        AudioFileMetadataEntry("ALBUM", "Same"),
        AudioFileMetadataEntry("ALBUM", "Different"),
        AudioFileMetadataEntry("ALBUM", "Same"),
        AudioFileMetadataEntry("EMPTY", ""),
        AudioFileMetadataEntry("ARTIST", "Björk"),
        AudioFileMetadataEntry(" TITLE ", "  padded value  "),
    )


def test_absent_comment_block_is_none(tmp_path):
    path = write_flac(tmp_path / "no-comments.flac")
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservation), result
    assert result.metadata_entries is None


def test_present_empty_comment_block_is_empty_tuple(tmp_path):
    path = write_flac(tmp_path / "empty.flac", vorbis_payload([]))
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservation), result
    assert result.metadata_entries == ()


def test_missing_field_is_not_an_error(tmp_path):
    payload = vorbis_payload([_entry("TITLE", "Only")])
    path = write_flac(tmp_path / "missing-field.flac", payload)
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservation), result
    assert result.metadata_entries == (AudioFileMetadataEntry("TITLE", "Only"),)


def test_underdeclared_comment_block_length_is_tolerated(tmp_path):
    payload = vorbis_payload([b"TITLE=Unchanged"])
    path = write_flac(tmp_path / "short-block-length.flac", payload)
    # the final block's three-byte length immediately precedes the payload
    with path.open("r+b") as fileobj:
        fileobj.seek(-(len(payload) + 3), os.SEEK_END)
        fileobj.write((len(payload) - 1).to_bytes(3, "big"))

    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservation), result
    assert result.metadata_entries == (AudioFileMetadataEntry("TITLE", "Unchanged"),)


@pytest.mark.parametrize(
    "payload, exception_type",
    [
        (vorbis_payload([b"TITLE=\xff"]), UnicodeDecodeError),
        (vorbis_payload([b"A=1"], vendor=b"\xff"), UnicodeDecodeError),
        (vorbis_payload([b"TITLE"]), MutagenError),
        (vorbis_payload([b"\xc3\xb6=x"]), MutagenError),
    ],
)
def test_repair_and_decoding_failures(tmp_path, payload, exception_type):
    path = write_flac(tmp_path / "bad.flac", payload)
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservationFailure)
    assert isinstance(result.error, exception_type)


@pytest.mark.parametrize(
    "raw_entry",
    [b"~=value", b"=value", b"\x01=value"],
)
def test_omitted_field_names_are_failures(tmp_path, raw_entry):
    path = write_flac(tmp_path / "omitted.flac", vorbis_payload([raw_entry]))
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservationFailure)
    assert isinstance(result.error, _IncompleteObservationError)


def test_unsupported_tilde_name_reports_incomplete_without_malformed_claim(tmp_path):
    path = write_flac(tmp_path / "tilde.flac", vorbis_payload([b"~=value"]))
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservationFailure)
    message = str(result.error).lower()
    assert "malformed" not in message
    assert "representable" in message or "unsupported" in message


def test_declared_and_retained_count_mismatch_fails(tmp_path):
    payload = vorbis_payload([b"~=dropped", b"TITLE=kept"], declared_count=2)
    path = write_flac(tmp_path / "count-mismatch.flac", payload)
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservationFailure)
    assert isinstance(result.error, _IncompleteObservationError)


def test_multiple_comment_blocks_are_rejected(tmp_path):
    first = vorbis_payload([_entry("TITLE", "First")])
    second = vorbis_payload([_entry("TITLE", "Second")])
    path = write_flac(tmp_path / "multiple.flac", first, second)
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservationFailure)
    assert "Vorbis comment blocks" in str(result.error)


def test_truncated_comment_payload_preserves_mutagen_failure(tmp_path):
    vendor = b"test"
    payload = (
        len(vendor).to_bytes(4, "little")
        + vendor
        + (1).to_bytes(4, "little")
        + (10).to_bytes(4, "little")
        + b"TITLE=x"
    )
    path = write_flac(tmp_path / "truncated.flac", payload)
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservationFailure)
    assert isinstance(result.error, MutagenError)


def test_filesystem_error_instance_is_preserved(tmp_path, monkeypatch):
    target = tmp_path / "missing.flac"
    failure = PermissionError(errno.EACCES, "injected denial", str(target))
    original_open = flac_metadata.os.open

    def fail_target(path, flags, *args, **kwargs):
        if Path(path) == target:
            raise failure
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(flac_metadata.os, "open", fail_target)
    result = observe_flac_metadata(target)
    assert isinstance(result, AudioFileObservationFailure)
    assert result.error is failure


def test_mutagen_error_instance_is_preserved(tmp_path, monkeypatch):
    path = write_flac(tmp_path / "any.flac")
    failure = MutagenError("injected parser failure")

    class FailingFLAC:
        def __init__(self, fileobj):
            raise failure

    monkeypatch.setattr(flac_metadata, "_StrictFLAC", FailingFLAC)
    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservationFailure)
    assert result.error is failure


@pytest.mark.parametrize("exception_type", [RuntimeError, KeyboardInterrupt])
def test_unexpected_exceptions_propagate(tmp_path, monkeypatch, exception_type):
    path = write_flac(tmp_path / "any.flac")
    failure = exception_type("injected")

    class FailingFLAC:
        def __init__(self, fileobj):
            raise failure

    monkeypatch.setattr(flac_metadata, "_StrictFLAC", FailingFLAC)
    with pytest.raises(exception_type) as caught:
        observe_flac_metadata(path)
    assert caught.value is failure


@pytest.mark.parametrize(
    "relative_path", [Path("song.flac"), Path("."), Path("dir/../song.flac")]
)
def test_relative_paths_are_rejected_before_io(relative_path):
    with pytest.raises(ValueError):
        observe_flac_metadata(relative_path)


def test_noncanonical_symlink_path_and_extension_independent(tmp_path):
    nested = tmp_path / "target" / "nested"
    nested.mkdir(parents=True)
    destination = nested / "song.data"
    shutil.copyfile(FIXTURE_AUDIO / "blackbird.flac", destination)
    (tmp_path / "link").symlink_to("target/nested", target_is_directory=True)

    observed_path = tmp_path / "link" / ".." / "nested" / "song.data"
    result = observe_flac_metadata(observed_path)
    assert isinstance(result, AudioFileObservation), result
    assert result.path == observed_path
    assert result.metadata_entries == CANONICAL_ENTRIES["blackbird.flac"]


def test_symlink_to_file_is_followed(tmp_path):
    target = tmp_path / "actual.flac"
    shutil.copyfile(FIXTURE_AUDIO / "minuet.flac", target)
    link = tmp_path / "alias.flac"
    link.symlink_to(target)

    result = observe_flac_metadata(link)
    assert isinstance(result, AudioFileObservation), result
    assert result.path == link
    assert result.metadata_entries == CANONICAL_ENTRIES["minuet.flac"]


def test_directory_is_rejected(tmp_path):
    result = observe_flac_metadata(tmp_path)
    assert isinstance(result, AudioFileObservationFailure)
    assert isinstance(result.error, OSError)


def test_fifo_is_rejected_without_waiting(tmp_path):
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    result = _observe_with_timeout(fifo)
    assert isinstance(result, AudioFileObservationFailure)
    assert isinstance(result.error, OSError)
    assert result.error.errno == errno.EINVAL


def test_symlink_to_fifo_is_rejected_without_waiting(tmp_path):
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    link = tmp_path / "pipe-link"
    link.symlink_to(fifo)
    result = _observe_with_timeout(link)
    assert isinstance(result, AudioFileObservationFailure)
    assert isinstance(result.error, OSError)
    assert result.error.errno == errno.EINVAL


def test_success_preserves_source_and_creates_no_output(tmp_path):
    target = tmp_path / "song.flac"
    shutil.copyfile(FIXTURE_AUDIO / "flamenco-road.flac", target)
    before_bytes = target.read_bytes()
    before_entries = sorted(entry.name for entry in tmp_path.iterdir())

    result = observe_flac_metadata(target)
    assert isinstance(result, AudioFileObservation)
    assert target.read_bytes() == before_bytes
    assert sorted(entry.name for entry in tmp_path.iterdir()) == before_entries


def test_failure_preserves_source_and_creates_no_output(tmp_path):
    path = write_flac(tmp_path / "bad.flac", vorbis_payload([b"TITLE"]))
    before_bytes = path.read_bytes()
    before_entries = sorted(entry.name for entry in tmp_path.iterdir())

    result = observe_flac_metadata(path)
    assert isinstance(result, AudioFileObservationFailure)
    assert path.read_bytes() == before_bytes
    assert sorted(entry.name for entry in tmp_path.iterdir()) == before_entries
