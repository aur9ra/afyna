# SPDX-License-Identifier: MPL-2.0

"""Characterize selected fields from observed Vorbis comments."""

from dataclasses import dataclass

from afyna.audio.observation import AudioFileMetadataEntry, AudioFileObservation


@dataclass(frozen=True)
class VorbisCommentFieldCharacterization:
    """Matching entries in observation order, including repetitions."""

    matching_entries: tuple[AudioFileMetadataEntry, ...]

    @property
    def single_stated_value(self) -> str | None:
        """Return the common nonblank value without normalizing it."""
        if not self.matching_entries:
            return None

        value = self.matching_entries[0].value
        if not value or value.isspace():
            return None
        if all(entry.value == value for entry in self.matching_entries):
            return value
        return None


@dataclass(frozen=True)
class VorbisCommentCharacterization:
    """Selected fields and the original observation that supports them."""

    observation: AudioFileObservation
    album_title: VorbisCommentFieldCharacterization
    album_artist_credit: VorbisCommentFieldCharacterization
    artist_credit: VorbisCommentFieldCharacterization


def characterize_vorbis_comment(
    observation: AudioFileObservation,
) -> VorbisCommentCharacterization:
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

    return VorbisCommentCharacterization(
        observation=observation,
        album_title=VorbisCommentFieldCharacterization(tuple(album_entries)),
        album_artist_credit=VorbisCommentFieldCharacterization(tuple(album_artist_entries)),
        artist_credit=VorbisCommentFieldCharacterization(tuple(artist_entries)),
    )
