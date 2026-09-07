"""
Content analysis Pydantic schemas.
Defines request/response models for text and image analysis endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class AnalyzeTextRequest(BaseModel):
    """Request body for text analysis."""
    text: str = Field(min_length=1, max_length=30000, description="Text to analyze")


class TokenImpact(BaseModel):
    """A single influential token with its impact score."""
    token: str
    impact: float = Field(description="Impact score (higher = more influential)")


class ModelScore(BaseModel):
    """Score from an individual model."""
    prediction: str
    confidence: float = Field(ge=0.0, le=1.0)


class ExplainabilityData(BaseModel):
    """Explainability output (SHAP tokens or Grad-CAM path)."""
    type: str = Field(description="shap | attention | lime | gradcam")
    influential_tokens: Optional[list[TokenImpact]] = None
    heatmap_path: Optional[str] = None  # For Grad-CAM (Phase 2)


class FactCheckResult(BaseModel):
    status: str = Field(description="matched | not_found | unavailable")
    claim: Optional[str] = None
    rating: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None


class AnalysisResponse(BaseModel):
    """
    Full analysis response with prediction, confidence, model scores,
    P(real), explainability data, and a disclaimer.
    """
    id: UUID
    content_type: str = Field(description="text | image | multimodal")
    prediction: str = Field(description="real | fake")
    confidence: float = Field(ge=0.0, le=1.0)
    low_confidence_flag: bool = Field(
        description="True if confidence is between 0.4–0.6 (manual review recommended)"
    )
    model_scores: dict[str, ModelScore] = Field(
        description="Scores from models that actually ran"
    )
    credibility_score: float = Field(
        ge=0.0, le=1.0,
        description="Estimated probability that the text is real"
    )
    explainability: Optional[ExplainabilityData] = None
    fact_check: Optional[FactCheckResult] = None
    disclaimer: str = "This is a model estimate. It does not replace professional fact-checking."
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisHistoryItem(BaseModel):
    """Simplified history list item."""
    id: UUID
    content_type: str
    prediction: str
    confidence: float
    credibility_score: float
    low_confidence_flag: bool
    input_preview: str
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedHistoryResponse(BaseModel):
    """Paginated analysis history response."""
    items: list[AnalysisHistoryItem]
    total: int
    page: int
    limit: int
