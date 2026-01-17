import os
import requests
from app.services.cache import (
    get_cached_similar,
    store_similar,
    get_cached_artist_tags,
    store_artist_tags,
    get_cached_track_tags,
    store_track_tags,
)

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
print(f"API Key loaded: {LASTFM_API_KEY is not None}")


def get_similar_tracks(artist: str, track: str, limit: int = 50):
    """
    Fetch similar tracks from Last.fm API.

    Args:
        artist: Artist name of the input track
        track: Track name to find similarities for
        limit: Maximum number of similar tracks to return (1 to 500)

    Returns:
        list:
            Similar track dictionaries from Last.fm, empty list if not found
    """
    # Check cache first
    try:
        cached = get_cached_similar(artist, track)
        if cached is not None:
            print(f"Cache HIT: {artist} - {track}")
            return cached[:limit]
        print(f"Cache MISS: {artist} - {track}")
    except Exception as e:
        print(f"Cache error: {e}")

    # Cache miss, call Last.fm with 500 track limit for caching
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "track.getsimilar",
        "artist": artist,
        "track": track,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": 500,
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "similartracks" in data and "track" in data["similartracks"]:
        tracks = data["similartracks"]["track"]
        try:
            store_similar(artist, track, tracks)
        except Exception as e:
            print(f"Cache store error: {e}")
        return tracks[:limit]  # return only what was requested
    return []


def get_artist_tags(artist: str) -> list:
    """
    Fetch top tags for an artist from Last.fm API.

    Args:
        artist: Artist name

    Returns:
        list: Tag dictionaries with 'name' and 'count' keys,
            empty list if not found
    """
    # Check cache first
    try:
        cached = get_cached_artist_tags(artist)
        if cached is not None:
            print(f"Tag cache HIT: {artist}")
            return cached
        print(f"Tag cache MISS: {artist}")
    except Exception as e:
        print(f"Tag cache error: {e}")

    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.getTopTags",
        "artist": artist,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "toptags" in data and "tag" in data["toptags"]:
        tags = data["toptags"]["tag"]
        try:
            store_artist_tags(artist, tags)
        except Exception as e:
            print(f"Tag cache store error: {e}")
        return tags
    return []


def get_track_tags(artist: str, track: str) -> list:
    """
    Fetch top tags for a track from Last.fm API.

    Args:
        artist: Artist name
        track: Track name

    Returns:
        list: Tag dictionaries with 'name' and 'count' keys,
            empty list if not found
    """
    # Check cache first
    try:
        cached = get_cached_track_tags(artist, track)
        if cached is not None:
            print(f"Track tag cache HIT: {artist} - {track}")
            return cached
        print(f"Track tag cache MISS: {artist} - {track}")
    except Exception as e:
        print(f"Track tag cache error: {e}")

    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "track.getTopTags",
        "artist": artist,
        "track": track,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "toptags" in data and "tag" in data["toptags"]:
        tags = data["toptags"]["tag"]
        try:
            store_track_tags(artist, track, tags)
        except Exception as e:
            print(f"Track tag cache store error: {e}")
        return tags
    return []
