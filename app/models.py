from pydantic import BaseModel

class TrackInput(BaseModel):
    """A single track from the user's listening history."""
    artist: str
    track: str

class TrackRecommendation(BaseModel):
    """A recommended track returned by the API."""
    track: str
    artist: str
    playcount: int
    url: str

class Explanation(BaseModel):
    """Explanation of why a track was recommended."""
    match_reason: str
    diversity_note: str
    popularity_note: str
    tag_match: list[str]

class RecommendationRequest(BaseModel):
    """Input parameters for generating a recommendation."""
    listening_history: list[TrackInput]
    diversity: float = 0.5   # 0.0 to 1.0
    popularity: str = "any"  # "obscure", "any", "popular"
    tags: list[str] = []     # up to 3 tags
    exclude_same_artist: bool = False
 
class RecommendationResponse(BaseModel):
    """Output returned by the /recommend endpoint."""
    recommendation: TrackRecommendation
    confidence_score: float
    explanation: Explanation