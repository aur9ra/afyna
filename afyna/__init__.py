# SPDX-License-Identifier: MPL-2.0

"""Read-only file discovery and metadata observation for afyna."""

from .discovery import DiscoveryError, FileDiscoveryInventory, discover_files
from .flac_metadata import (
    AudioFileMetadataEntry,
    AudioFileObservation,
    AudioFileObservationFailure,
    observe_flac_metadata,
)

__all__ = [
    "AudioFileMetadataEntry",
    "AudioFileObservation",
    "AudioFileObservationFailure",
    "DiscoveryError",
    "FileDiscoveryInventory",
    "discover_files",
    "observe_flac_metadata",
]
