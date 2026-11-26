# SPDX-License-Identifier: MPL-2.0

"""Internal parser for unframed Vorbis-comment payloads."""

from mutagen._vorbis import VCommentDict


class _IncompleteObservationError(Exception):
    """Raised when every declared comment field cannot be represented."""


class _StrictVorbisComment(VCommentDict):
    """Parse a Vorbis-comment payload without repairing or omitting fields.

    Mutagen's default ``errors='replace'`` invents names for missing ``=``
    separators and silently drops names it rejects.  Strict decoding rejects
    repairs.  Re-reading the declared entry count also detects names the
    parser omitted, such as the valid ``~`` name unsupported by this version.
    """

    def __init__(self, data=None, *args, **kwargs):
        self.declared_comment_count = None
        super().__init__(data, *args, **kwargs)

    def load(self, fileobj, errors="strict", framing=False):
        start = fileobj.tell()
        super().load(fileobj, errors=errors, framing=framing)
        end = fileobj.tell()

        # re-read the declared count without buffering the payload so Mutagen
        # keeps the supplied stream's short-read behavior
        fileobj.seek(start)
        vendor_length = int.from_bytes(fileobj.read(4), "little")
        fileobj.seek(vendor_length, 1)
        declared_count = int.from_bytes(fileobj.read(4), "little")
        fileobj.seek(end)

        self.declared_comment_count = declared_count
        if declared_count != len(self):
            raise _IncompleteObservationError(
                "Vorbis comment declared "
                f"{declared_count} entries but only {len(self)} were "
                "representable; some field names may be unsupported"
            )
