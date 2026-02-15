from fastapi import APIRouter, HTTPException
from app.models import (
    RecommendationRequest,
    RecommendationResponse,
    TrackInput,
    TrackRecommendation,
    Explanation,
)
from app.services.scoring import get_recommendation
import time

router = APIRouter()


@router.post("/recommend")
def recommend(data: RecommendationRequest) -> RecommendationResponse:
    start_time = time.time()

    # Convert to dict for get_recommendation()
    history = [{"artist": t.artist, "track": t.track} for t in data.listening_history]
    result = get_recommendation(
        listening_history=history,
        diversity=data.diversity,
        popularity=data.popularity,
        tags=data.tags,
        tag_match_type=data.tag_match_type,
        exclude_same_artist=data.exclude_same_artist,
        baseline=data.baseline,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    top_track = result["recommendation"]

    # Track response time
    elapsed = time.time() - start_time
    print(
        f"[{data.listening_history[0].artist} - {data.listening_history[0].track} + {len(data.listening_history) - 1} more] "
        f"tags={data.tags}, tag_match={data.tag_match_type}, "
        f"elapsed={elapsed:.2f}s"
    )

    # Build match reason with source tracks
    sources = top_track.get("sources", [])
    if len(sources) == 1:
        match_reason = f"Similar to {sources[0]}"
    else:
        match_reason = f"Similar to {', '.join(sources[:-1])} and {sources[-1]}"

    # Build diversity note
    if data.diversity == 0.5:
        diversity_note = (
            "Diversity set to neutral (0.5). Results ranked by similarity only."
        )
    elif data.diversity < 0.5:
        diversity_note = (
            f"Diversity set to {data.diversity}. Favouring closely similar tracks."
        )
    else:
        diversity_note = (
            f"Diversity set to {data.diversity}. Boosting less obvious picks."
        )

    # Build popularity note
    if data.popularity == "any":
        popularity_note = "No popularity preference applied"
    elif data.popularity == "popular":
        popularity_note = "Popular tracks boosted in ranking"
    else:
        popularity_note = "Obscure tracks boosted in ranking"

    # Build tag match note
    matched_tags = top_track.get("matched_tags", [])
    if data.tags:
        unmatched_tags = [
            t for t in data.tags if t.lower() not in [m.lower() for m in matched_tags]
        ]
    else:
        unmatched_tags = []

    return RecommendationResponse(
        recommendation=TrackRecommendation(
            track=top_track["track"],
            artist=top_track["artist"],
            playcount=top_track["playcount"],
            url=top_track["url"],
        ),
        top_5=[
            TrackRecommendation(
                track=c["track"],
                artist=c["artist"],
                playcount=c["playcount"],
                url=c["url"],
            )
            for c in result["top_5"]
        ],
        confidence_score=top_track["score"],
        explanation=Explanation(
            match_reason=match_reason,
            diversity_note=diversity_note,
            popularity_note=popularity_note,
            tag_match=matched_tags,
            tag_unmatched=unmatched_tags,
        ),
        skipped_inputs=[
            TrackInput(artist=s["artist"], track=s["track"])
            for s in result["skipped_inputs"]
        ],
    )
