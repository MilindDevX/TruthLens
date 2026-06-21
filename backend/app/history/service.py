"""
History service for querying user's past analyses.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.history.models import AnalysisHistory
from app.content.schemas import (
    AnalysisResponse, AnalysisHistoryItem,
    PaginatedHistoryResponse, ModelScore, ExplainabilityData,
)


async def get_user_history(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    limit: int = 20,
) -> PaginatedHistoryResponse:
    """
    Get paginated analysis history for a user.
    Ordered by most recent first.
    """
    offset = (page - 1) * limit

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(AnalysisHistory).where(
            AnalysisHistory.user_id == user_id
        )
    )
    total = count_result.scalar_one()

    # Fetch page
    result = await db.execute(
        select(AnalysisHistory)
        .where(AnalysisHistory.user_id == user_id)
        .order_by(AnalysisHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    records = result.scalars().all()

    items = [
        AnalysisHistoryItem(
            id=r.id,
            content_type=r.content_type.value if hasattr(r.content_type, 'value') else r.content_type,
            prediction=r.prediction,
            confidence=r.confidence_score,
            credibility_score=r.credibility_score,
            low_confidence_flag=r.low_confidence_flag,
            input_preview=r.input_preview or "",
            model_version=r.model_version,
            created_at=r.created_at,
        )
        for r in records
    ]

    return PaginatedHistoryResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
    )


async def get_analysis_by_id(
    db: AsyncSession,
    analysis_id: UUID,
    user_id: UUID,
) -> AnalysisResponse | None:
    """
    Get a single analysis by ID, scoped to the requesting user.
    Returns None if not found or user doesn't own it.
    """
    result = await db.execute(
        select(AnalysisHistory).where(
            AnalysisHistory.id == analysis_id,
            AnalysisHistory.user_id == user_id,
        )
    )
    record = result.scalar_one_or_none()

    if record is None:
        return None

    # Reconstruct model scores
    model_scores = {}
    if record.model_scores:
        for k, v in record.model_scores.items():
            model_scores[k] = ModelScore(**v)

    explainability = None
    if record.explainability_data:
        explainability = ExplainabilityData(**record.explainability_data)

    return AnalysisResponse(
        id=record.id,
        content_type=record.content_type.value if hasattr(record.content_type, 'value') else record.content_type,
        prediction=record.prediction,
        confidence=record.confidence_score,
        low_confidence_flag=record.low_confidence_flag,
        model_scores=model_scores,
        credibility_score=record.credibility_score,
        explainability=explainability,
        model_version=record.model_version,
        created_at=record.created_at,
    )
