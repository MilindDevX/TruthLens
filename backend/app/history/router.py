"""
History router — provides paginated analysis history and individual result lookup.
Follows router discipline: delegates to history service only.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.content.schemas import AnalysisResponse, PaginatedHistoryResponse
from app.history.service import get_user_history, get_analysis_by_id

router = APIRouter(prefix="/history", tags=["Analysis History"])


@router.get("", response_model=PaginatedHistoryResponse)
async def list_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated analysis history for the authenticated user.
    Ordered by most recent first.
    """
    return await get_user_history(db, current_user.id, page, limit)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_history_item(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single analysis result by ID.
    Only returns results owned by the authenticated user.
    """
    result = await get_analysis_by_id(db, analysis_id, current_user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )
    return result
