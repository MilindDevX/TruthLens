"""
Admin router — model reload with locking.
Only accessible by users with admin role.
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import Literal, Optional

from app.auth.dependencies import require_admin
from app.users.models import User
from app.ml.model_loader import reload_text_model, get_latest_version

router = APIRouter(prefix="/admin", tags=["Admin"])

# Global lock for safe model reloading
_model_reload_lock = asyncio.Lock()


class ReloadModelRequest(BaseModel):
    """Request to reload a specific model type."""
    model_type: Literal["text", "image"] = Field(description="Which model to reload")
    version: Optional[str] = Field(default=None, description="Version to load (omit for latest)")


class ReloadModelResponse(BaseModel):
    """Response after model reload."""
    status: str
    model_type: str
    version: str
    has_baseline: bool = False
    has_advanced: bool = False
    message: str


@router.post("/reload-model", response_model=ReloadModelResponse)
async def reload_model(
    body: ReloadModelRequest,
    request: Request,
    admin: User = Depends(require_admin),
):
    """
    Reload a model from disk (safe hot-swap).

    Security:
    - Admin-only access
    - Acquires async lock to prevent concurrent reloads
    - Swaps model reference atomically on app.state

    This prevents:
    - Race conditions during reload
    - Memory leaks from orphaned models
    - In-flight request failures
    """
    if _model_reload_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Model reload already in progress",
        )

    async with _model_reload_lock:
        try:
            if body.model_type == "text":
                result = await reload_text_model(
                    request.app.state,
                    version=body.version,
                )

                return ReloadModelResponse(
                    status="success",
                    model_type="text",
                    version=result["version"],
                    has_baseline=result["has_baseline"],
                    has_advanced=result["has_advanced"],
                    message=(
                        f"Text model reloaded to {result['version']} — "
                        f"baseline={'✓' if result['has_baseline'] else '✗'}, "
                        f"advanced={'✓' if result['has_advanced'] else '✗'}"
                    ),
                )
            else:
                # Image model reload (Phase 2)
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Image model reload not yet implemented",
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model reload failed: {str(e)}",
            )
