# SPDX-License-Identifier: MPL-2.0

"""Read-only file discovery and metadata observation for afyna."""

from .discovery import DiscoveryError, FileDiscoveryInventory, discover_files
from .flac_metadata import (
    AudioFileMetadataEntry,
    AudioFileObservation,
    AudioFileObservationFailure,
    observe_flac_metadata,
)
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
