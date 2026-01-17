from fastapi import APIRouter, HTTPException
from app.models import (
    RecommendationRequest,
    RecommendationResponse,
    TrackInput,
    TrackRecommendation,
    Explanation,
)
from app.services.scoring import get_recommendation

router = APIRouter()


@router.post("/recommend")
def recommend(data: RecommendationRequest) -> RecommendationResponse:
    # Convert to dict for get_recommendation()
    history = [{"artist": t.artist, "track": t.track} for t in data.listening_history]
    result = get_recommendation(
        listening_history=history,
        diversity=data.diversity,
        popularity=data.popularity,
        tags=data.tags,
        tag_match_type=data.tag_match_type,
        exclude_same_artist=data.exclude_same_artist,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    top_track = result["recommendation"]

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
            match_reason=f"Appeared in {top_track['appearances']} similarity lists",
            diversity_note=f"Diversity set to {data.diversity}",
            popularity_note=f"Popularity preference: {data.popularity}",
            tag_match=top_track.get("matched_tags", []),
        ),
        skipped_inputs=[
            TrackInput(artist=s["artist"], track=s["track"])
            for s in result["skipped_inputs"]
        ],
    )
