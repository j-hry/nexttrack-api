import pytest
from unittest.mock import patch
from app.services.scoring import (
    calculate_recency_weight,
    calculate_score,
    get_recommendation,
)


# --- Recency weighting ---
def test_recency_weight_oldest_track():
    """First track in a 3-track history gets lowest weight."""
    weight = calculate_recency_weight(position=0, total=3)
    assert weight == pytest.approx(1 / 3)


def test_recency_weight_newest_track():
    """Last track in a 3-track history gets weight 1.0."""
    weight = calculate_recency_weight(position=2, total=3)
    assert weight == pytest.approx(1.0)


# --- Diversity scoring ---
def test_low_diversity_boosts_top_ranked():
    """At diversity=0.0, top-ranked candidate scores higher than at neutral diversity."""
    score_low_div = calculate_score(
        recency_weight=1.0, rank=0, total_results=50, diversity=0.0
    )
    score_neutral = calculate_score(
        recency_weight=1.0, rank=0, total_results=50, diversity=0.5
    )
    assert score_low_div > score_neutral


def test_high_diversity_narrows_rank_gap():
    """At diversity=1.0, the score gap between top and bottom rank is smaller than at 0.0."""
    top_low = calculate_score(
        recency_weight=1.0, rank=0, total_results=50, diversity=0.0
    )
    bottom_low = calculate_score(
        recency_weight=1.0, rank=49, total_results=50, diversity=0.0
    )
    gap_low = top_low - bottom_low

    top_high = calculate_score(
        recency_weight=1.0, rank=0, total_results=50, diversity=1.0
    )
    bottom_high = calculate_score(
        recency_weight=1.0, rank=49, total_results=50, diversity=1.0
    )
    gap_high = top_high - bottom_high

    assert gap_high < gap_low


# --- Exclude same artist ---
@patch("app.services.scoring.get_similar_tracks")
def test_exclude_same_artist_filters_correctly(mock_similar):
    """Candidates by input artists are removed when exclude_same_artist=True."""
    mock_similar.return_value = [
        {
            "artist": {"name": "Radiohead"},
            "name": "Karma Police",
            "playcount": 1000,
            "url": "",
        },
        {"artist": {"name": "Coldplay"}, "name": "Yellow", "playcount": 800, "url": ""},
    ]

    history = [
        {"artist": "Radiohead", "track": "Creep"},
        {"artist": "Muse", "track": "Hysteria"},
        {"artist": "Oasis", "track": "Wonderwall"},
    ]

    result = get_recommendation(history, exclude_same_artist=True)
    recommended_artists = [t["artist"] for t in result["top_5"]]
    assert "Radiohead" not in recommended_artists


# --- Tag matching ---
@patch("app.services.scoring.get_artist_tags")
@patch("app.services.scoring.get_similar_tracks")
def test_tag_match_boosts_score(mock_similar, mock_tags):
    """Candidates with matching tags score higher than those without."""
    mock_similar.return_value = [
        {
            "artist": {"name": "Artist A"},
            "name": "Track A",
            "playcount": 500,
            "url": "",
        },
        {
            "artist": {"name": "Artist B"},
            "name": "Track B",
            "playcount": 500,
            "url": "",
        },
    ]

    def fake_tags(artist):
        if artist == "Artist A":
            return [{"name": "rock", "count": 100}]
        return [{"name": "jazz", "count": 100}]

    mock_tags.side_effect = fake_tags

    history = [
        {"artist": "Someone", "track": "Song 1"},
        {"artist": "Another", "track": "Song 2"},
        {"artist": "Third", "track": "Song 3"},
    ]

    result = get_recommendation(history, tags=["rock"], tag_match_type="artist")
    assert result["recommendation"]["artist"] == "Artist A"
