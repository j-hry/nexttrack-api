from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_SIMILAR = [
    {
        "artist": {"name": "Artist A"},
        "name": "Track A",
        "playcount": 5000,
        "url": "http://a",
    },
    {
        "artist": {"name": "Artist B"},
        "name": "Track B",
        "playcount": 100,
        "url": "http://b",
    },
    {
        "artist": {"name": "Artist C"},
        "name": "Track C",
        "playcount": 3000,
        "url": "http://c",
    },
]

VALID_BODY = {
    "listening_history": [
        {"artist": "Radiohead", "track": "Creep"},
        {"artist": "Muse", "track": "Hysteria"},
        {"artist": "Oasis", "track": "Wonderwall"},
    ],
    "diversity": 0.5,
    "popularity": "any",
    "tags": [],
    "tag_match_type": "artist",
    "exclude_same_artist": False,
}


@patch("app.services.scoring.get_similar_tracks")
def test_valid_request_returns_full_response(mock_similar):
    """Valid request returns 200 with all expected response fields."""
    mock_similar.return_value = MOCK_SIMILAR

    response = client.post("/api/v1/recommend", json=VALID_BODY)
    assert response.status_code == 200

    data = response.json()
    assert "recommendation" in data
    assert "top_5" in data
    assert "confidence_score" in data
    assert "explanation" in data
    assert "skipped_inputs" in data

    rec = data["recommendation"]
    assert "track" in rec
    assert "artist" in rec
    assert "playcount" in rec
    assert "url" in rec

    explanation = data["explanation"]
    assert "match_reason" in explanation
    assert "diversity_note" in explanation
    assert "popularity_note" in explanation
    assert "tag_match" in explanation


@patch("app.services.scoring.get_similar_tracks")
def test_no_similar_tracks_returns_404(mock_similar):
    """When all input tracks return no similar results, API returns 404."""
    mock_similar.return_value = []

    response = client.post("/api/v1/recommend", json=VALID_BODY)
    assert response.status_code == 404


@patch("app.services.scoring.get_similar_tracks")
def test_popularity_parameter_affects_ranking(mock_similar):
    """Popular vs obscure popularity setting produces different top recommendations."""
    mock_similar.return_value = MOCK_SIMILAR

    body_popular = {**VALID_BODY, "popularity": "popular"}
    body_obscure = {**VALID_BODY, "popularity": "obscure"}

    response_popular = client.post("/api/v1/recommend", json=body_popular)
    response_obscure = client.post("/api/v1/recommend", json=body_obscure)

    top_popular = response_popular.json()["recommendation"]["artist"]
    top_obscure = response_obscure.json()["recommendation"]["artist"]

    assert top_popular != top_obscure
