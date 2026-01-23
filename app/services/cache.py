import os
import json
import psycopg2

CACHE_TTL_DAYS = 7


def get_connection():
    """
    Create a connection to the PostgreSQL database.

    Returns:
        psycopg2.connection: Active database connection
    """
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def get_cached_similar(artist: str, track: str):
    """
    Look up cached similar tracks for a given artist/track pair.

    Args:
        artist: Artist name
        track: Track name

    Returns:
        list: Cached similar tracks if found, None if not cached
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT similar_tracks
            FROM similar_tracks_cache 
            WHERE artist = %s AND track = %s
            AND cached_at > NOW() - INTERVAL '%s days'
            """,
            (artist.lower(), track.lower(), CACHE_TTL_DAYS),
        )
        row = cur.fetchone()
        if row is not None:
            return row[0]  # returns [] if tags are empty
        return None  # returns None if row does not exist
    finally:
        conn.close()


def store_similar(artist: str, track: str, similar_tracks: list):
    """
    Store similar tracks in the cache.

    Args:
        artist: Artist name
        track: Track name
        similar_tracks: List of similar track dictionaries from Last.fm
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO similar_tracks_cache (artist, track, similar_tracks)
            VALUES (%s, %s, %s)
            ON CONFLICT (artist, track)
            DO UPDATE SET
                similar_tracks = EXCLUDED.similar_tracks,
                cached_at = CURRENT_TIMESTAMP
            """,
            (artist.lower(), track.lower(), json.dumps(similar_tracks)),
        )
        conn.commit()
    finally:
        conn.close()


def get_cached_artist_tags(artist: str):
    """
    Look up cached tags for a given artist.

    Args:
        artist: Artist name

    Returns:
        list: Cached tags if found, None if not cached
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT tags
            FROM artist_tags_cache
            WHERE artist = %s
            AND cached_at > NOW() - INTERVAL '%s days'
            """,
            (artist.lower(), CACHE_TTL_DAYS),
        )
        row = cur.fetchone()
        if row is not None:
            return row[0]  # returns [] if tags are empty
        return None  # returns None if row does not exist
    finally:
        conn.close()


def store_artist_tags(artist: str, tags: list):
    """
    Store artist tags in the cache.

    Args:
        artist: Artist name
        tags: List of tag dictionaries from Last.fm
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO artist_tags_cache (artist, tags)
            VALUES (%s, %s)
            ON CONFLICT (artist)
            DO UPDATE SET
                tags = EXCLUDED.tags,
                cached_at = CURRENT_TIMESTAMP
            """,
            (artist.lower(), json.dumps(tags)),
        )
        conn.commit()
    finally:
        conn.close()


def get_cached_track_tags(artist: str, track: str):
    """
    Look up cached tags for a given artist/track pair.

    Args:
        artist: Artist name
        track: Track name

    Returns:
        list: Cached tags if found, None if not cached
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT tags
            FROM track_tags_cache
            WHERE artist = %s AND track = %s
            AND cached_at > NOW() - INTERVAL '%s days'
            """,
            (artist.lower(), track.lower(), CACHE_TTL_DAYS),
        )
        row = cur.fetchone()
        if row is not None:
            return row[0]  # returns [] if tags are empty
        return None  # returns None if row does not exist
    finally:
        conn.close()


def store_track_tags(artist: str, track: str, tags: list):
    """
    Store track tags in the cache.

    Args:
        artist: Artist name
        track: Track name
        tags: List of tag dictionaries from Last.fm
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO track_tags_cache (artist, track, tags)
            VALUES (%s, %s, %s)
            ON CONFLICT (artist, track)
            DO UPDATE SET
                tags = EXCLUDED.tags,
                cached_at = CURRENT_TIMESTAMP
            """,
            (artist.lower(), track.lower(), json.dumps(tags)),
        )
        conn.commit()
        print(f"Track tag STORED: '{artist.lower()}' - '{track.lower()}'")
    except Exception as e:
        print(f"Track tag STORE FAILED: {e}")
    finally:
        conn.close()
