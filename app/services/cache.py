import os
import json
import psycopg2


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
            """,
            (artist.lower(), track.lower()),
        )
        row = cur.fetchone()
        if row:
            return row[0]
        return None
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
