from pydantic import BaseModel, Field, field_validator
from typing import Literal


class TrackInput(BaseModel):
    """A single track from the user's listening history."""

    artist: str = Field(..., min_length=1)
    track: str = Field(..., min_length=1)

    @field_validator("artist", "track")
    @classmethod
    def must_not_be_blank(cls, v):
        if not v.strip():
            raise ValueError("Must not be empty or whitespace")
        return v


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
    tag_unmatched: list[str]


class RecommendationRequest(BaseModel):
    """Input parameters for generating a recommendation."""

    listening_history: list[TrackInput] = Field(..., min_length=3, max_length=10)
    diversity: float = Field(default=0.5, ge=0.0, le=1.0)
    popularity: Literal["obscure", "any", "popular"] = "any"
    tags: list[str] = Field(default=[], max_length=3)
    tag_match_type: Literal["artist", "track"] = "artist"
    exclude_same_artist: bool = False
    baseline: bool = False

    @field_validator("tags")
    @classmethod
    def tags_must_be_non_empty(cls, v):
        for tag in v:
            if not tag.strip():
                raise ValueError("Tags must be non-empty strings")
        return v


class RecommendationResponse(BaseModel):
    """Output returned by the /recommend endpoint."""

    recommendation: TrackRecommendation
    top_5: list[TrackRecommendation]
    confidence_score: float
    explanation: Explanation
    skipped_inputs: list[TrackInput]
