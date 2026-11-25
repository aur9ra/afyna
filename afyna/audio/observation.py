# SPDX-License-Identifier: MPL-2.0

"""Audio metadata observation records."""

from dataclasses import dataclass
from pathlib import Path


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
