from fastapi import APIRouter, HTTPException
from app.models import (
    RecommendationRequest,
    RecommendationResponse,
    TrackRecommendation,
    Explanation,
)
from app.services.scoring import get_recommendation

router = APIRouter()


@router.post("/recommend")
def recommend(data: RecommendationRequest) -> RecommendationResponse:
    # Convert to dict for get_recommendation()
    history = [{"artist": t.artist, "track": t.track} for t in data.listening_history]
    result = get_recommendation(history, data.diversity)

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
        confidence_score=top_track["score"],
        explanation=Explanation(
            match_reason=f"Appeared in {top_track['appearances']} similarity lists",
            diversity_note=f"Diversity set to {data.diversity}",
            popularity_note="Based on Last.fm playcount",
            tag_match=[],
        ),
    )
