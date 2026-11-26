# SPDX-License-Identifier: MPL-2.0

"""Vorbis-comment payload parsing tests."""

from io import BytesIO

from afyna.audio.metadata_formats.vorbis_comment.parsing import _StrictVorbisComment
from tests.support.flac_bytes import vorbis_payload


def test_parses_ordered_entries_at_offset_and_leaves_trailing_bytes_unread():
    prefix = b"prefix"
    trailing = b"trailing bytes"
    payload = vorbis_payload([b"title=First", b"ALBUM=Other", b"title=First"])
    stream = BytesIO(prefix + payload + trailing)
    stream.seek(len(prefix))

    comment = _StrictVorbisComment(stream)

    assert list(comment) == [
        ("title", "First"),
        ("ALBUM", "Other"),
        ("title", "First"),
    ]
    assert comment.declared_comment_count == 3
    assert stream.tell() == len(prefix) + len(payload)
    assert stream.read() == trailing
