# SPDX-License-Identifier: MPL-2.0

"""Characterize selected fields from observed Vorbis comments."""

from afyna.audio.characterization import (
    AudioFileMetadataCharacterization,
    MetadataFieldCharacterization,
)
from afyna.audio.observation import AudioFileObservation


def characterize_vorbis_comment(
    observation: AudioFileObservation,
) -> AudioFileMetadataCharacterization:
    """Interpret an observation already designated as Vorbis comments."""
    album_entries = []
    album_artist_entries = []
    artist_entries = []
    for entry in observation.metadata_entries or ():
        # guard against Unicode uppercasing that maps non-ASCII letters to ASCII
        if not entry.name.isascii():
            continue
        name = entry.name.upper()
        if name == "ALBUM":
            album_entries.append(entry)
        elif name in ("ALBUMARTIST", "ALBUM ARTIST", "ALBUM_ARTIST"):
            album_artist_entries.append(entry)
        elif name == "ARTIST":
            artist_entries.append(entry)

    return AudioFileMetadataCharacterization(
        observation=observation,
        album_title=MetadataFieldCharacterization(tuple(album_entries)),
        album_artist_credit=MetadataFieldCharacterization(tuple(album_artist_entries)),
        artist_credit=MetadataFieldCharacterization(tuple(artist_entries)),
    )
