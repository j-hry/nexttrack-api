import os
import time
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


def lastfm_request(params: dict, context: str, max_retries: int = 2):
    """
    Make a request to the Last.fm API with retry logic for rate limiting.

    Args:
        params: Query parameters for the API call
        context: Description for logging (e.g. "artist tags for 'Pink Floyd'")
        max_retries: Number of retries on rate limit / temporary errors

    Returns:
        dict: Parsed JSON response, or None if request failed
    """
    url = "https://ws.audioscrobbler.com/2.0/"

    for attempt in range(max_retries + 1):
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(
                f"Last.fm HTTP {response.status_code} ({context}): {response.text[:200]}"
            )
            if response.status_code == 502 and attempt < max_retries:
                print(f"Retrying in 1s... (attempt {attempt + 2})")
                time.sleep(1)
                continue
            return None

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"Last.fm non-JSON response ({context}): {response.text[:200]}")
            if attempt < max_retries:
                print(f"Retrying in 1s... (attempt {attempt + 2})")
                time.sleep(1)
                continue
            return None

        # Check for Last.fm API-level errors
        if "error" in data:
            error_code = data["error"]
            error_msg = data.get("message", "Unknown error")
            print(f"Last.fm error {error_code} ({context}): {error_msg}")

            if error_code in (11, 16, 29) and attempt < max_retries:
                print(f"Retrying in 1s... (attempt {attempt + 2})")
                time.sleep(1)
                continue
            return None

        return data

    return None


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

    params = {
        "method": "track.getsimilar",
        "artist": artist,
        "track": track,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": 500,
    }

    data = lastfm_request(params, f"similar tracks for '{artist}' - '{track}'")
    if data is None:
        return []

    if "similartracks" in data and "track" in data["similartracks"]:
        tracks = data["similartracks"]["track"]
        try:
            store_similar(artist, track, tracks)
        except Exception as e:
            print(f"Cache store error: {e}")
        return tracks[:limit]
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

    params = {
        "method": "artist.getTopTags",
        "artist": artist,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }

    data = lastfm_request(params, f"artist tags for '{artist}'")
    if data is None:
        return []

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

    params = {
        "method": "track.getTopTags",
        "artist": artist,
        "track": track,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }

    data = lastfm_request(params, f"track tags for '{artist}' - '{track}'")
    if data is None:
        return []

    if "toptags" in data and "tag" in data["toptags"]:
        tags = data["toptags"]["tag"]
        try:
            store_track_tags(artist, track, tags)
        except Exception as e:
            print(f"Track tag cache store error: {e}")
        return tags
    return []
