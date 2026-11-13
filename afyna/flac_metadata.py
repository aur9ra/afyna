# SPDX-License-Identifier: MPL-2.0

"""Read-only FLAC Vorbis-comment observation through Mutagen."""

import errno
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from mutagen import MutagenError
from mutagen.flac import FLAC, VCFLACDict


@dataclass(frozen=True)
class AudioFileMetadataEntry:
    name: str
    value: str


@dataclass(frozen=True)
class AudioFileObservation:
    path: Path
    metadata_entries: tuple[AudioFileMetadataEntry, ...] | None


@dataclass(frozen=True)
class AudioFileObservationFailure:
    path: Path
    error: Exception


_VORBIS_COMMENT_BLOCK_CODE = 4


class _IncompleteObservationError(Exception):
    """Raised when every declared comment field cannot be represented."""


class _StrictVorbisComment(VCFLACDict):
    """Vorbis comment block parsed without repairing or omitting fields.

    Mutagen's default ``errors='replace'`` invents names for missing ``=``
    separators and silently drops names it rejects.  Strict decoding rejects
    repairs.  Re-reading the declared entry count also detects names the
    parser omitted, such as the valid ``~`` name unsupported by this version.
    """

    def __init__(self, data=None, *args, **kwargs):
        self.declared_comment_count = None
        super().__init__(data, *args, **kwargs)

    def load(self, data, errors="strict", framing=False):
        start = data.tell()
        super().load(data, errors=errors, framing=framing)
        end = data.tell()

        # re-read the declared count after a successful normal parse
        # the comment payload itself is not buffered, so Mutagen keeps its
        # ordinary short-read behavior
        data.seek(start)
        vendor_length = int.from_bytes(data.read(4), "little")
        data.seek(vendor_length, 1)
        declared_count = int.from_bytes(data.read(4), "little")
        data.seek(end)

        self.declared_comment_count = declared_count
        if declared_count != len(self):
            raise _IncompleteObservationError(
                "Vorbis comment declared "
                f"{declared_count} entries but only {len(self)} were "
                "representable; some field names may be unsupported"
            )


class _StrictFLAC(FLAC):
    METADATA_BLOCKS = list(FLAC.METADATA_BLOCKS)
    METADATA_BLOCKS[_VORBIS_COMMENT_BLOCK_CODE] = _StrictVorbisComment


def observe_flac_metadata(
    path: Path,
) -> AudioFileObservation | AudioFileObservationFailure:
    """Observe Vorbis-comment fields in a FLAC file.

    ``metadata_entries`` is ``None`` when no Vorbis-comment block is present
    and an empty tuple when a present block has no entries.  Field names,
    values, order, conflicts and duplicates are preserved exactly.
    """
    if not path.is_absolute():
        raise ValueError("path must be an absolute path")

    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    except OSError as error:
        return AudioFileObservationFailure(path, error)

    try:
        try:
            file_status = os.fstat(descriptor)
        except OSError as error:
            return AudioFileObservationFailure(path, error)

        if not stat.S_ISREG(file_status.st_mode):
            return AudioFileObservationFailure(
                path,
                OSError(errno.EINVAL, "not a regular file", os.fspath(path)),
            )

        try:
            with os.fdopen(descriptor, "rb") as fileobj:
                descriptor = -1
                return _observe_opened_file(path, fileobj)
        except (
            OSError,
            UnicodeError,
            MutagenError,
            _IncompleteObservationError,
        ) as error:
            return AudioFileObservationFailure(path, error)
    finally:
        if descriptor != -1:
            os.close(descriptor)


def _observe_opened_file(path: Path, fileobj) -> AudioFileObservation:
    flac = _StrictFLAC(fileobj)
    comment_blocks = [
        block
        for block in flac.metadata_blocks
        if block.code == _VORBIS_COMMENT_BLOCK_CODE
    ]

    # FLAC.tags exposes only the first block, reject any additional parsed
    # comment blocks rather than silently selecting one
    if len(comment_blocks) > 1:
        raise _IncompleteObservationError(
            f"{len(comment_blocks)} Vorbis comment blocks present; "
            "only one can be observed"
        )

    if not comment_blocks:
        return AudioFileObservation(path, None)

    entries = tuple(
        AudioFileMetadataEntry(name, value) for name, value in comment_blocks[0]
    )
    return AudioFileObservation(path, entries)
