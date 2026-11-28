# SPDX-License-Identifier: MPL-2.0

"""Textual evidence for the musical metadata concepts Afyna supports."""

from dataclasses import dataclass

from .observation import AudioFileMetadataEntry, AudioFileObservation


@dataclass(frozen=True)
class MetadataFieldCharacterization:
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
class AudioFileMetadataCharacterization:
    """Selected fields and the original observation that supports them."""

    observation: AudioFileObservation
    album_title: MetadataFieldCharacterization
    album_artist_credit: MetadataFieldCharacterization
    artist_credit: MetadataFieldCharacterization
