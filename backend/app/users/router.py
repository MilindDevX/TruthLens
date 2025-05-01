"""
User profile router.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.users.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return UserResponse.model_validate(current_user)
