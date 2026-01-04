import os
import requests
from app.services.cache import get_cached_similar, store_similar

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
        if cached:
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
        return tracks[:limit] # return only what was requested
    return []
