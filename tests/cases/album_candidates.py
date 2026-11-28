# SPDX-License-Identifier: MPL-2.0

"""Exact-title album-candidate formation tests using constructed evidence."""

from pathlib import Path

from afyna import form_exact_title_album_candidates
from afyna.audio.characterization import (
    AudioFileMetadataCharacterization,
    MetadataFieldCharacterization,
)
from afyna.audio.metadata_formats.vorbis_comment.characterization import (
    characterize_vorbis_comment,
)
from afyna.audio.observation import AudioFileMetadataEntry, AudioFileObservation


def _album(value: str) -> AudioFileMetadataEntry:
    return AudioFileMetadataEntry("ALBUM", value)


def _characterization(
    path: str, *entries: AudioFileMetadataEntry
) -> AudioFileMetadataCharacterization:
    return characterize_vorbis_comment(AudioFileObservation(Path(path), tuple(entries)))


def test_empty_input_produces_empty_formation():
    result = form_exact_title_album_candidates(())

    assert result.candidates == ()
    assert result.unplaced == ()


def test_interleaved_titles_order_candidates_and_members():
    first_x = _characterization("first.flac", _album("X"))
    y = _characterization("y.flac", _album("Y"))
    second_x = _characterization("second.flac", _album("X"))
    z = _characterization("z.flac", _album("Z"))
    third_x = _characterization("third.flac", _album("X"))

    result = form_exact_title_album_candidates([first_x, y, second_x, z, third_x])

    assert result.unplaced == ()
    assert [candidate.album_title for candidate in result.candidates] == [
        "X",
        "Y",
        "Z",
    ]
    assert [candidate.characterizations for candidate in result.candidates] == [
        (first_x, second_x, third_x),
        (y,),
        (z,),
    ]


def test_singleton_title_forms_a_candidate():
    only = _characterization("only.flac", _album("Only"))

    result = form_exact_title_album_candidates([only])

    assert len(result.candidates) == 1
    assert result.candidates[0].album_title == "Only"
    assert result.candidates[0].characterizations == (only,)
    assert result.unplaced == ()


def test_one_shot_iterable_is_consumed_once():
    first = _characterization("first.flac", _album("A"))
    untitled = _characterization(
        "untitled.flac", AudioFileMetadataEntry("TITLE", "Track")
    )
    second = _characterization("second.flac", _album("B"))

    result = form_exact_title_album_candidates(
        characterization for characterization in (first, untitled, second)
    )

    assert [candidate.album_title for candidate in result.candidates] == ["A", "B"]
    assert result.candidates[0].characterizations == (first,)
    assert result.candidates[1].characterizations == (second,)
    assert result.unplaced == (untitled,)


def test_literal_title_differences_form_separate_candidates():
    titles = [
        "Album",
        "album",
        "Album!",
        "Album ",
        " Album",
        "Album\u00a0",
        "Bj\u00f6rk",
        "Bjo\u0308rk",
    ]
    characterizations = [
        _characterization(f"{index}.flac", _album(title))
        for index, title in enumerate(titles)
    ]

    result = form_exact_title_album_candidates(characterizations)

    assert [candidate.album_title for candidate in result.candidates] == titles
    for candidate, characterization in zip(
        result.candidates, characterizations, strict=True
    ):
        assert candidate.characterizations == (characterization,)


def test_repeated_identical_title_entries_remain_eligible():
    repeated = _characterization("repeated.flac", _album("Same"), _album("Same"))

    result = form_exact_title_album_candidates([repeated])

    assert result.candidates[0].album_title == "Same"
    assert result.candidates[0].characterizations == (repeated,)


def test_missing_blank_mixed_and_distinct_titles_are_unplaced():
    cases = [
        _characterization("missing.flac", AudioFileMetadataEntry("TITLE", "Track")),
        _characterization("empty.flac", _album("")),
        _characterization("whitespace.flac", _album("\u00a0\u2003")),
        _characterization("mixed.flac", _album(""), _album("Title")),
        _characterization("distinct.flac", _album("First"), _album("Second")),
    ]

    result = form_exact_title_album_candidates(cases)

    assert result.candidates == ()
    assert result.unplaced == tuple(cases)
    for actual, expected in zip(result.unplaced, cases, strict=True):
        assert actual is expected


def test_raw_matching_entry_does_not_attach_untitled_observation():
    ambiguous = _characterization("ambiguous.flac", _album("Shared"), _album("Other"))
    matching = _characterization("matching.flac", _album("Shared"))

    result = form_exact_title_album_candidates([ambiguous, matching])

    assert [candidate.album_title for candidate in result.candidates] == ["Shared"]
    assert result.candidates[0].characterizations == (matching,)
    assert result.unplaced == (ambiguous,)


def test_shared_titles_stay_together_despite_artist_evidence():
    shared = [
        _characterization("absent.flac", _album("Shared")),
        _characterization(
            "album-artist.flac",
            _album("Shared"),
            AudioFileMetadataEntry("ALBUMARTIST", "One"),
        ),
        _characterization(
            "differing.flac",
            _album("Shared"),
            AudioFileMetadataEntry("ALBUMARTIST", "One"),
            AudioFileMetadataEntry("ALBUMARTIST", "Two"),
        ),
        _characterization(
            "repeated.flac",
            _album("Shared"),
            AudioFileMetadataEntry("ALBUM ARTIST", "One"),
            AudioFileMetadataEntry("ALBUM_ARTIST", "One"),
        ),
        _characterization(
            "multivalued.flac",
            _album("Shared"),
            AudioFileMetadataEntry("ARTIST", "One"),
            AudioFileMetadataEntry("ARTIST", "Two"),
        ),
    ]

    result = form_exact_title_album_candidates(shared)

    assert result.unplaced == ()
    assert len(result.candidates) == 1
    assert result.candidates[0].characterizations == tuple(shared)


def test_differing_album_artist_credits_do_not_split_shared_title():
    queen = _characterization(
        "queen.flac",
        _album("Greatest Hits"),
        AudioFileMetadataEntry("ALBUMARTIST", "Queen"),
        AudioFileMetadataEntry("ARTIST", "Queen"),
    )
    police = _characterization(
        "police.flac",
        _album("Greatest Hits"),
        AudioFileMetadataEntry("ALBUMARTIST", "The Police"),
        AudioFileMetadataEntry("ARTIST", "The Police"),
    )
    fleetwood_mac = _characterization(
        "fleetwood-mac.flac",
        _album("Greatest Hits"),
        AudioFileMetadataEntry("ALBUMARTIST", "Fleetwood Mac"),
        AudioFileMetadataEntry("ARTIST", "Fleetwood Mac"),
    )
    characterizations = [queen, police, fleetwood_mac]

    result = form_exact_title_album_candidates(characterizations)

    assert result.unplaced == ()
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.album_title == "Greatest Hits"
    assert len(candidate.characterizations) == len(characterizations)
    for actual, expected in zip(
        candidate.characterizations, characterizations, strict=True
    ):
        assert actual is expected


def test_differing_track_artist_credits_do_not_split_shared_title():
    queen = _characterization(
        "various-queen.flac",
        _album("Compilation"),
        AudioFileMetadataEntry("ALBUMARTIST", "Various Artists"),
        AudioFileMetadataEntry("ARTIST", "Queen"),
    )
    police = _characterization(
        "various-police.flac",
        _album("Compilation"),
        AudioFileMetadataEntry("ALBUMARTIST", "Various Artists"),
        AudioFileMetadataEntry("ARTIST", "The Police"),
    )
    fleetwood_mac = _characterization(
        "various-fleetwood-mac.flac",
        _album("Compilation"),
        AudioFileMetadataEntry("ALBUMARTIST", "Various Artists"),
        AudioFileMetadataEntry("ARTIST", "Fleetwood Mac"),
    )
    characterizations = [queen, police, fleetwood_mac]

    result = form_exact_title_album_candidates(characterizations)

    assert result.unplaced == ()
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.album_title == "Compilation"
    assert len(candidate.characterizations) == len(characterizations)
    for actual, expected in zip(
        candidate.characterizations, characterizations, strict=True
    ):
        assert actual is expected


def test_directly_constructed_characterizations_are_retained():
    empty_field = MetadataFieldCharacterization(())
    first_album_entry = AudioFileMetadataEntry("Album Title", "Shared")
    first = AudioFileMetadataCharacterization(
        observation=AudioFileObservation(
            Path("first.audio"),
            (first_album_entry, AudioFileMetadataEntry("Track Title", "Track")),
        ),
        album_title=MetadataFieldCharacterization((first_album_entry,)),
        album_artist_credit=empty_field,
        artist_credit=empty_field,
    )
    untitled = AudioFileMetadataCharacterization(
        observation=AudioFileObservation(
            Path("untitled.audio"), (AudioFileMetadataEntry("Track Title", "Track"),)
        ),
        album_title=empty_field,
        album_artist_credit=empty_field,
        artist_credit=empty_field,
    )
    second_album_entry = AudioFileMetadataEntry("Album Title", "Shared")
    second = AudioFileMetadataCharacterization(
        observation=AudioFileObservation(Path("second.audio"), (second_album_entry,)),
        album_title=MetadataFieldCharacterization((second_album_entry,)),
        album_artist_credit=empty_field,
        artist_credit=empty_field,
    )

    result = form_exact_title_album_candidates([first, untitled, second])

    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.album_title == "Shared"
    assert len(candidate.characterizations) == 2
    assert candidate.characterizations[0] is first
    assert candidate.characterizations[1] is second
    assert len(result.unplaced) == 1
    assert result.unplaced[0] is untitled


def test_repeated_occurrences_are_retained_without_deduplication():
    repeated_title = _characterization("repeated.flac", _album("Same"), _album("Same"))
    untitled = _characterization(
        "untitled.flac", AudioFileMetadataEntry("TITLE", "Track")
    )
    other = _characterization("other.flac", _album("Other"))

    result = form_exact_title_album_candidates(
        [repeated_title, untitled, other, repeated_title, untitled]
    )

    assert [candidate.album_title for candidate in result.candidates] == [
        "Same",
        "Other",
    ]
    assert result.candidates[0].characterizations == (
        repeated_title,
        repeated_title,
    )
    assert result.candidates[1].characterizations == (other,)
    assert result.unplaced == (untitled, untitled)
    assert result.unplaced[0] is untitled
    assert result.unplaced[1] is untitled


def test_different_paths_do_not_split_a_shared_title_candidate():
    first = _characterization("disc-a/track.flac", _album("Shared"))
    second = _characterization("disc-b/track.flac", _album("Shared"))

    result = form_exact_title_album_candidates([first, second])

    assert len(result.candidates) == 1
    assert result.candidates[0].characterizations == (first, second)


def test_same_path_occurrences_remain_distinct():
    first = _characterization("shared.flac", _album("First"))
    second = _characterization("shared.flac", _album("Second"))
    repeated_first = _characterization("shared.flac", _album("First"))

    result = form_exact_title_album_candidates([first, second, repeated_first])

    assert [candidate.album_title for candidate in result.candidates] == [
        "First",
        "Second",
    ]
    assert result.candidates[0].characterizations == (first, repeated_first)
    assert result.candidates[1].characterizations == (second,)
