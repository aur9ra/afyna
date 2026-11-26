# SPDX-License-Identifier: MPL-2.0

"""Characterization tests using directly constructed observations."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from afyna.audio.metadata_formats.vorbis_comment.characterization import (
    VorbisCommentFieldCharacterization,
    characterize_vorbis_comment,
)
from afyna.audio.observation import AudioFileMetadataEntry, AudioFileObservation


def _assert_field(
    field: VorbisCommentFieldCharacterization,
    entries: tuple[AudioFileMetadataEntry, ...],
    value: str | None,
) -> None:
    assert field.matching_entries == entries
    for actual, expected in zip(field.matching_entries, entries, strict=True):
        assert actual is expected
    assert field.single_stated_value == value


def test_interleaved_entries_preserve_alias_order_duplicates_and_literal_values():
    padded_credit = "\t Isis \u2003"
    spaced_credit = AudioFileMetadataEntry("aLbUm ArTiSt", padded_credit)
    artist = AudioFileMetadataEntry("aRtIsT", "Isis")
    album = AudioFileMetadataEntry("aLbUm", "Panopticon")
    underscored_credit = AudioFileMetadataEntry("ALBum_arTIST", padded_credit)
    other = AudioFileMetadataEntry("TITLE", "So Did We")
    repeated_album = AudioFileMetadataEntry("aLbUm", "Panopticon")
    compact_credit = AudioFileMetadataEntry("AlbumArtist", padded_credit)
    observation = AudioFileObservation(
        Path("not-a-flac.mp3"),
        (
            spaced_credit,
            artist,
            album,
            underscored_credit,
            other,
            repeated_album,
            compact_credit,
        ),
    )

    result = characterize_vorbis_comment(observation)

    assert result.observation is observation
    _assert_field(result.album_title, (album, repeated_album), "Panopticon")
    _assert_field(
        result.album_artist_credit,
        (spaced_credit, underscored_credit, compact_credit),
        padded_credit,
    )
    _assert_field(result.artist_credit, (artist,), "Isis")


def test_near_miss_and_unrelated_names_do_not_match():
    entries = tuple(
        AudioFileMetadataEntry(name, "Ignored")
        for name in (
            "ARTI\u017fT",  # long s folds to ASCII s
            "ALBUMART\u0131ST",  # dotless i uppercases to ASCII I
            " ALBUM",
            "ALBUM ",
            "AL BUM",
            "ALBUM-ARTIST",
            "ALBUM  ARTIST",
            "ALBUM\tARTIST",
            "ALBUM__ARTIST",
            "ARTISTS",
            "TITLE",
        )
    )
    observation = AudioFileObservation(Path("record"), entries)

    result = characterize_vorbis_comment(observation)

    assert result.observation is observation
    _assert_field(result.album_title, (), None)
    _assert_field(result.album_artist_credit, (), None)
    _assert_field(result.artist_credit, (), None)


@pytest.mark.parametrize("entries", [None, ()], ids=["absent", "present-empty"])
def test_no_entries_retains_original_metadata_state(
    entries: tuple[AudioFileMetadataEntry, ...] | None,
):
    observation = AudioFileObservation(Path("record"), entries)

    result = characterize_vorbis_comment(observation)

    assert result.observation is observation
    _assert_field(result.album_title, (), None)
    _assert_field(result.album_artist_credit, (), None)
    _assert_field(result.artist_credit, (), None)


def test_artist_does_not_supply_album_artist_credit():
    artist = AudioFileMetadataEntry("ARTIST", "Bj\u00f6rk")
    observation = AudioFileObservation(Path("record"), (artist,))

    result = characterize_vorbis_comment(observation)

    assert result.observation is observation
    _assert_field(result.album_title, (), None)
    _assert_field(result.album_artist_credit, (), None)
    _assert_field(result.artist_credit, (artist,), "Bj\u00f6rk")


@pytest.mark.parametrize(
    "value", ["", "\u00a0\u2003"], ids=["empty", "unicode-whitespace"]
)
def test_identical_blank_values_are_retained_but_not_reported_as_single(value: str):
    first = AudioFileMetadataEntry("ALBUM", value)
    second = AudioFileMetadataEntry("ALBUM", value)
    observation = AudioFileObservation(Path("record"), (first, second))

    result = characterize_vorbis_comment(observation)

    assert result.observation is observation
    _assert_field(result.album_title, (first, second), None)


@pytest.mark.parametrize(
    "variant", ["tool", " Tool ", ""], ids=["case", "padding", "empty"]
)
def test_album_artist_aliases_with_literal_conflicts_do_not_choose_a_spelling(
    variant: str,
):
    album = AudioFileMetadataEntry("ALBUM", "Lateralus")
    artist = AudioFileMetadataEntry("ARTIST", "Tool")
    first = AudioFileMetadataEntry("ALBUM ARTIST", "Tool")
    second = AudioFileMetadataEntry("ALBUMARTIST", variant)
    observation = AudioFileObservation(Path("record"), (album, artist, first, second))

    result = characterize_vorbis_comment(observation)

    assert result.observation is observation
    _assert_field(result.album_title, (album,), "Lateralus")
    _assert_field(result.album_artist_credit, (first, second), None)
    _assert_field(result.artist_credit, (artist,), "Tool")


def test_distinct_artist_credits_leave_the_other_fields_unaffected():
    first = AudioFileMetadataEntry("ARTIST", "Cult of Luna")
    album = AudioFileMetadataEntry("ALBUM", "Mariner")
    album_artist = AudioFileMetadataEntry(
        "ALBUM_ARTIST", "Cult of Luna & Julie Christmas"
    )
    second = AudioFileMetadataEntry("artist", "Julie Christmas")
    observation = AudioFileObservation(
        Path("record"), (first, album, album_artist, second)
    )

    result = characterize_vorbis_comment(observation)

    assert result.observation is observation
    _assert_field(result.album_title, (album,), "Mariner")
    _assert_field(
        result.album_artist_credit,
        (album_artist,),
        "Cult of Luna & Julie Christmas",
    )
    _assert_field(result.artist_credit, (first, second), None)


def test_characterization_records_are_frozen():
    observation = AudioFileObservation(Path("record"), None)
    result = characterize_vorbis_comment(observation)

    with pytest.raises(FrozenInstanceError):
        setattr(result, "observation", None)
    with pytest.raises(FrozenInstanceError):
        setattr(result.album_title, "matching_entries", ())
