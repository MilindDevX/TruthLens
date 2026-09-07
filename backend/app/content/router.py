"""
Content analysis router.
Follows router discipline: delegates everything to service layer.
Injects TextInferenceService via DI.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.content.schemas import AnalyzeTextRequest, AnalysisResponse, FactCheckResult
from app.content.service import analyze_text, fact_check_text
from app.ml.dependencies import get_text_inference
from app.ml.text_inference import TextInferenceService

router = APIRouter(prefix="/analyze", tags=["Content Analysis"])


@router.post("/fact-check", response_model=FactCheckResult)
async def fact_check_text_endpoint(
    body: AnalyzeTextRequest,
    current_user: User = Depends(get_current_user),
):
    """Look up a published fact check; no local model is required."""
    return await fact_check_text(body.text)


@router.post("/text", response_model=AnalysisResponse)
async def analyze_text_endpoint(
    body: AnalyzeTextRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    inference_service: TextInferenceService = Depends(get_text_inference),
):
    """
    Analyze text content for fake-news signals.

    Pipeline:
    1. Validate input (max 5K words / 30K chars)
    2. Check dedup cache (skip inference if identical content was analyzed before)
    3. Run available models
    4. Compute estimated P(real)
    5. Generate available explainability data
    6. Save to history

    Returns:
    - prediction (real/fake)
    - confidence score
    - per-model breakdown
    - estimated P(real)
    - explainability data
    - mandatory disclaimer
    """
    return await analyze_text(
        db=db,
        text=body.text,
        user_id=current_user.id,
        request=request,
        inference_service=inference_service,
    )
