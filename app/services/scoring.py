from app.services.lastfm import get_similar_tracks


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
        diversity_modifier = 1.0 + (1 - normalized_rank) * (0.5 - diversity) * 0.6
    else:
        diversity_modifier = 1.0 + normalized_rank * (diversity - 0.5) * 0.6

    return recency_adjusted * diversity_modifier  # final score


def get_recommendation(listening_history: list[dict], diversity: float = 0.5) -> dict:
    """
    Generate recommendation from listening history.

    Args:
        listening_history: List of {"artist": str, "track": str} dicts,
            ordered oldest to newest
        diversity: User preference for variety (0.0 = similar, 1.0 = diverse)

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
            else:
                candidate_pool[key] = {
                    "artist": candidate["artist"]["name"],
                    "track": candidate["name"],
                    "playcount": int(candidate.get("playcount", 0)),
                    "url": candidate.get("url", ""),
                    "score": score,
                    "appearances": 1,
                }

    if not candidate_pool:
        return {"error": "No similar tracks found", "skipped": skipped}

    # Filter out input tracks
    input_keys = {(t["artist"], t["track"]) for t in listening_history}
    candidates = [c for key, c in candidate_pool.items() if key not in input_keys]

    candidates.sort(key=lambda x: x["score"], reverse=True)

    return {
        "recommendation": candidates[0] if candidates else None,
        "top_5": candidates[:5],
        "skipped_inputs": skipped,
    }
