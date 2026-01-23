from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _valid_request(**overrides):
    """Build a valid request body, then apply any overrides."""
    base = {
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
    base.update(overrides)
    return base


# --- Listening history constraints ---
def test_too_few_tracks():
    """Request with fewer than 3 tracks returns 422."""
    body = _valid_request(
        listening_history=[
            {"artist": "Radiohead", "track": "Creep"},
            {"artist": "Muse", "track": "Hysteria"},
        ]
    )
    response = client.post("/api/v1/recommend", json=body)
    assert response.status_code == 422


def test_too_many_tracks():
    """Request with more than 10 tracks returns 422."""
    tracks = [{"artist": f"Artist {i}", "track": f"Track {i}"} for i in range(11)]
    body = _valid_request(listening_history=tracks)
    response = client.post("/api/v1/recommend", json=body)
    assert response.status_code == 422


# --- TrackInput constraints ---
def test_empty_artist_rejected():
    """Empty artist string returns 422."""
    body = _valid_request(
        listening_history=[
            {"artist": "", "track": "Creep"},
            {"artist": "Muse", "track": "Hysteria"},
            {"artist": "Oasis", "track": "Wonderwall"},
        ]
    )
    response = client.post("/api/v1/recommend", json=body)
    assert response.status_code == 422


def test_whitespace_track_rejected():
    """Whitespace-only track string returns 422."""
    body = _valid_request(
        listening_history=[
            {"artist": "Radiohead", "track": "   "},
            {"artist": "Muse", "track": "Hysteria"},
            {"artist": "Oasis", "track": "Wonderwall"},
        ]
    )
    response = client.post("/api/v1/recommend", json=body)
    assert response.status_code == 422


# --- Diversity constraints ---
def test_diversity_above_range():
    """Diversity value above 1.0 returns 422."""
    body = _valid_request(diversity=1.5)
    response = client.post("/api/v1/recommend", json=body)
    assert response.status_code == 422


def test_diversity_below_range():
    """Diversity value below 0.0 returns 422."""
    body = _valid_request(diversity=-0.1)
    response = client.post("/api/v1/recommend", json=body)
    assert response.status_code == 422


# --- Popularity constraints ---
def test_invalid_popularity_value():
    """Invalid popularity value returns 422."""
    body = _valid_request(popularity="extreme")
    response = client.post("/api/v1/recommend", json=body)
    assert response.status_code == 422


# --- Tag constraints ---
def test_too_many_tags():
    """More than 3 tags returns 422."""
    body = _valid_request(tags=["rock", "pop", "jazz", "metal"])
    response = client.post("/api/v1/recommend", json=body)
    assert response.status_code == 422


def test_empty_tag_string_rejected():
    """A tag list containing an empty string returns 422."""
    body = _valid_request(tags=["rock", ""])
    response = client.post("/api/v1/recommend", json=body)
    assert response.status_code == 422


# --- Tag match type constraints ---
def test_invalid_tag_match_type():
    """Invalid tag_match_type value returns 422."""
    body = _valid_request(tag_match_type="album")
    response = client.post("/api/v1/recommend", json=body)
    assert response.status_code == 422
