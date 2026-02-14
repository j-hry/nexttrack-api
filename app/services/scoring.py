from app.services.lastfm import get_similar_tracks, get_artist_tags, get_track_tags
from app.services.utils import normalize_text


def calculate_recency_weight(position: int, total: int) -> float:
    """
    Calculate weight based on track position in listening history.

    Args:
        position: Index of track in history (0 = oldest)
        total: Total number of tracks in history

    Returns:
        float:
            Weight from 0.0 to 1.0 (higher = more recent track)
    """
    return (position + 1) / total


def calculate_score(
    recency_weight: float, rank: int, total_results: int, diversity: float
) -> float:
    """
    Combine recency, rank, and diversity into a final score.

    Args:
        recency_weight: Weight based on track position in history
            (0.0 to 1.0, higher = more recent)
        rank: Position in similarity results (0 = most similar)
        total_results: Total number of similar tracks returned
        diversity: User preference for variety (0.0 = similar, 1.0 = diverse)

    Returns:
        float: Weighted score combining all factors (higher = better recommendation)
    """
    normalized_rank = rank / total_results  # normalize from 0-1 (0 = most similar)
    base_score = 1.0 - (normalized_rank * 0.5)  # top rank = 1.0, bottom = 0.5
    recency_adjusted = base_score * recency_weight

    # Apply diversity adjustments
    if diversity <= 0.5:
        diversity_modifier = 1.0 + (1 - normalized_rank) * (0.5 - diversity) * 2.0
    else:
        diversity_modifier = 1.0 + normalized_rank * (diversity - 0.5) * 2.0

    return recency_adjusted * diversity_modifier  # final score


def get_recommendation(
    listening_history: list[dict],
    diversity: float = 0.5,
    popularity: str = "any",
    tags: list[str] = None,
    tag_match_type: str = "artist",
    exclude_same_artist: bool = False,
) -> dict:
    """
    Generate recommendation from listening history.

    Args:
        listening_history: List of {"artist": str, "track": str} dicts,
            ordered oldest to newest
        diversity: User preference for variety (0.0 = similar, 1.0 = diverse)
        popularity: User preference for track popularity ("obscure", "any", "popular")
        tags: List of tag strings to match against (e.g. ["rock", "80s"]).
            Candidates with matching tags get a score boost.
        exclude_same_artist: If True, filter out tracks by artists already in
            the listening history
    Returns:
        dict: recommendation (top track or None), top_5 (list of top 5 tracks),
            skipped_inputs (tracks with no similar results)
    """
    candidate_pool = {}
    skipped = []

    for i, input_track in enumerate(listening_history):
        recency_weight = calculate_recency_weight(i, len(listening_history))
        similar = get_similar_tracks(input_track["artist"], input_track["track"])

        if not similar:
            skipped.append(input_track)
            continue

        for rank, candidate in enumerate(similar):
            key = (candidate["artist"]["name"], candidate["name"])
            score = calculate_score(
                recency_weight=recency_weight,
                rank=rank,
                total_results=len(similar),
                diversity=diversity,
            )

            if key in candidate_pool:
                candidate_pool[key]["score"] += score
                candidate_pool[key]["appearances"] += 1
                candidate_pool[key]["sources"].append(
                    f"{input_track['artist']} – {input_track['track']}"
                )
            else:
                candidate_pool[key] = {
                    "artist": candidate["artist"]["name"],
                    "track": candidate["name"],
                    "playcount": int(candidate.get("playcount", 0)),
                    "url": candidate.get("url", ""),
                    "score": score,
                    "appearances": 1,
                    "sources": [f"{input_track['artist']} – {input_track['track']}"],
                }

    if not candidate_pool:
        return {"error": "No similar tracks found", "skipped": skipped}

    # Filter out input tracks
    input_keys = {
        (normalize_text(t["artist"]), normalize_text(t["track"]))
        for t in listening_history
    }
    candidates = [
        c
        for key, c in candidate_pool.items()
        if (normalize_text(key[0]), normalize_text(key[1])) not in input_keys
    ]

    # Filter out tracks by input artists if exclude_same_artist
    if exclude_same_artist:
        input_artists = {normalize_text(t["artist"]) for t in listening_history}
        candidates = [
            c for c in candidates if normalize_text(c["artist"]) not in input_artists
        ]

    # Apply tag matching adjustment
    if tags and candidates:
        normalized_tags = {t.lower() for t in tags}

        if tag_match_type == "artist":
            unique_artists = {c["artist"] for c in candidates[:30]}
            artist_tags_map = {}
            for artist in unique_artists:
                artist_tags = get_artist_tags(artist)
                artist_tags_map[artist] = {t["name"].lower() for t in artist_tags}

            for c in candidates[:30]:
                candidate_tags = artist_tags_map.get(c["artist"], set())
                matching = normalized_tags & candidate_tags
                if matching:
                    tag_modifier = 1.0 + len(matching) * 0.15
                    c["score"] *= tag_modifier
                    c["matched_tags"] = list(matching)

        else:  # "track"
            for c in candidates[:30]:
                track_tags = get_track_tags(c["artist"], c["track"])
                candidate_tags = {t["name"].lower() for t in track_tags}
                matching = normalized_tags & candidate_tags
                if matching:
                    tag_modifier = 1.0 + len(matching) * 0.15
                    c["score"] *= tag_modifier
                    c["matched_tags"] = list(matching)

    # Apply popularity adjustment
    if popularity != "any" and candidates:
        playcounts = [c["playcount"] for c in candidates]
        max_pc = max(playcounts)
        min_pc = min(playcounts)
        pc_range = max_pc - min_pc if max_pc != min_pc else 1

        for c in candidates:
            normalized_pc = (c["playcount"] - min_pc) / pc_range

            if popularity == "popular":
                pc_modifier = 1.0 + normalized_pc * 0.3
            else:  # "obscure"
                pc_modifier = 1.0 + (1 - normalized_pc) * 0.3

            c["score"] *= pc_modifier

    # Apply diversity-based appearance adjustment
    if diversity > 0.5:
        max_appearances = max(c["appearances"] for c in candidates)
        if max_appearances > 1:
            for c in candidates:
                appearance_penalty = (
                    1.0
                    - (c["appearances"] - 1) / max_appearances * (diversity - 0.5) * 0.6
                )
                c["score"] *= appearance_penalty

    candidates.sort(key=lambda x: x["score"], reverse=True)

    return {
        "recommendation": candidates[0] if candidates else None,
        "top_5": candidates[:5],
        "skipped_inputs": skipped,
    }
