# SPDX-License-Identifier: MPL-2.0

"""Read-only FLAC Vorbis-comment observation through Mutagen."""

import errno
import os
import stat
from pathlib import Path

from mutagen import MutagenError
from mutagen.flac import FLAC, VCFLACDict

from ...metadata_formats.vorbis_comment.parsing import (
    _IncompleteObservationError,
    _StrictVorbisComment,
)
from ...observation import (
    AudioFileMetadataEntry,
    AudioFileObservation,
    AudioFileObservationFailure,
)

_VORBIS_COMMENT_BLOCK_CODE = 4


# strict defaults must precede VCFLACDict's replacement defaults
# Mutagen passes the stream positionally despite the base parameter names differing
class _StrictVCFLACDict(_StrictVorbisComment, VCFLACDict):  # pyright: ignore[reportIncompatibleMethodOverride]
    """Adapt strict payload parsing to Mutagen's FLAC block reader."""


class _StrictFLAC(FLAC):
    METADATA_BLOCKS = list(FLAC.METADATA_BLOCKS)
    METADATA_BLOCKS[_VORBIS_COMMENT_BLOCK_CODE] = _StrictVCFLACDict


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
