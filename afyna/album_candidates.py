# SPDX-License-Identifier: MPL-2.0

"""Form album candidates from exact stated album titles."""

from collections.abc import Iterable
from dataclasses import dataclass

from .audio.characterization import AudioFileMetadataCharacterization


@dataclass(frozen=True)
class ExactTitleAlbumCandidate:
    """Characterizations sharing one exact stated album title.

    A candidate establishes exact stated-title agreement and joint
    consideration only. It does not establish common album membership,
    release identity, completeness, or import eligibility.
    """

    album_title: str
    characterizations: tuple[AudioFileMetadataCharacterization, ...]


@dataclass(frozen=True)
class ExactTitleAlbumCandidateFormationResult:
    """Exact-title candidates and characterizations without a title summary.

    Candidates are ordered by their first contributing characterization.
    Both collections preserve input order and retain every occurrence.
    """

    candidates: tuple[ExactTitleAlbumCandidate, ...]
    unplaced: tuple[AudioFileMetadataCharacterization, ...]


def form_exact_title_album_candidates(
    characterizations: Iterable[AudioFileMetadataCharacterization],
) -> ExactTitleAlbumCandidateFormationResult:
    """Group characterizations by exact non-``None`` stated album title.

    Titles use literal equality, so punctuation, case, whitespace, and
    Unicode representation differences stay separate. Album-artist and
    artist evidence do not affect assignment. A characterization without a
    single stated title is retained individually in ``unplaced``.
    """
    grouped: dict[str, list[AudioFileMetadataCharacterization]] = {}
    unplaced: list[AudioFileMetadataCharacterization] = []
    for characterization in characterizations:
        title = characterization.album_title.single_stated_value
        if title is None:
            unplaced.append(characterization)
        else:
            grouped.setdefault(title, []).append(characterization)

    candidates = tuple(
        ExactTitleAlbumCandidate(album_title=title, characterizations=tuple(group))
        for title, group in grouped.items()
    )
    return ExactTitleAlbumCandidateFormationResult(
        candidates=candidates,
        unplaced=tuple(unplaced),
    )
