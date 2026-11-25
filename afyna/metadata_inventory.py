# SPDX-License-Identifier: MPL-2.0

"""Observe metadata for a captured file-discovery baseline without rediscovery."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .discovery import FileDiscoveryInventory
from .flac_metadata import (
    AudioFileObservation,
    AudioFileObservationFailure,
    observe_flac_metadata,
)


@dataclass(frozen=True)
class DiscoveryDiagnostic:
    """A discovery diagnostic with path and exception bindings."""

    path: Path
    error: OSError


@dataclass(frozen=True)
class MetadataObservationOccurrence:
    """One baseline file occurrence and its optional observation outcome.

    ``outcome`` is ``None`` when the observed pathname was not selected for
    observation.
    """

    path: Path
    outcome: AudioFileObservation | AudioFileObservationFailure | None


@dataclass(frozen=True)
class MetadataObservationInventory:
    """Historical metadata evidence for a captured discovery baseline.

    Preserves occurrence order and multiplicity. Discovery diagnostics
    are retained separately from observation failures.
    """

    occurrences: tuple[MetadataObservationOccurrence, ...]
    discovery_errors: tuple[DiscoveryDiagnostic, ...]


def _has_flac_suffix(path: Path) -> bool:
    return path.suffix.lower() == ".flac"


def observe_metadata_inventory(
    discovery_inventory: FileDiscoveryInventory,
    *,
    flac_observer: Callable[
        [Path], AudioFileObservation | AudioFileObservationFailure
    ] = observe_flac_metadata,
) -> MetadataObservationInventory:
    """Observe FLAC metadata over an independently captured discovery baseline.

    Select occurrences by case-insensitive pathname suffix, passing each
    original Path to flac_observer in baseline order.

    Retain returned successes and failures unchanged. Reject None observer
    results. Raised exceptions propagate.
    """

    baseline_paths = tuple(discovery_inventory.files)
    discovery_errors = tuple(
        DiscoveryDiagnostic(path=error.path, error=error.error)
        for error in discovery_inventory.errors
    )

    occurrences = []
    for path in baseline_paths:
        outcome = None
        if _has_flac_suffix(path):
            outcome = flac_observer(path)
            if outcome is None:
                raise TypeError("flac_observer must not return None")
        occurrences.append(MetadataObservationOccurrence(path=path, outcome=outcome))

    return MetadataObservationInventory(
        occurrences=tuple(occurrences),
        discovery_errors=discovery_errors,
    )
