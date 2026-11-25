# SPDX-License-Identifier: MPL-2.0

"""Read-only file discovery and metadata observation for afyna."""

from .audio.file_formats.flac.metadata import observe_flac_metadata
from .audio.observation import (
    AudioFileMetadataEntry,
    AudioFileObservation,
    AudioFileObservationFailure,
)
from .discovery import DiscoveryError, FileDiscoveryInventory, discover_files
from .metadata_inventory import (
    DiscoveryDiagnostic,
    MetadataObservationInventory,
    MetadataObservationOccurrence,
    observe_metadata_inventory,
)

__all__ = [
    "AudioFileMetadataEntry",
    "AudioFileObservation",
    "AudioFileObservationFailure",
    "DiscoveryDiagnostic",
    "DiscoveryError",
    "FileDiscoveryInventory",
    "MetadataObservationInventory",
    "MetadataObservationOccurrence",
    "discover_files",
    "observe_flac_metadata",
    "observe_metadata_inventory",
]
