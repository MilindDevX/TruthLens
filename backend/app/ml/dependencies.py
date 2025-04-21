"""
FastAPI dependency injection for ML model access.

Design decisions:
- Models are loaded ONCE at startup into app.state
- All access goes through Depends() — never global imports
- This makes models testable (can inject mocks) and avoids globals
- Returns TextInferenceService (not raw model objects)
"""

from fastapi import Request, HTTPException, status
from app.ml.text_inference import TextInferenceService
from app.ml.drift_monitor import DriftMonitor
from typing import Optional


def get_text_inference(request: Request) -> TextInferenceService:
    """
    FastAPI dependency to get the text inference service.

    Returns the TextInferenceService stored on app.state at startup.
    Raises 503 if no models are loaded — never returns None.

    Usage:
        @router.post("/analyze/text")
        async def analyze(
            inference: TextInferenceService = Depends(get_text_inference),
        ):
            result = await inference.predict(text)
    """
    service = getattr(request.app.state, "text_inference", None)

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Text inference service not available. Models may not be loaded.",
        )

    return service


def get_text_inference_optional(request: Request) -> Optional[TextInferenceService]:
    """
    Optional variant — returns None instead of raising 503.
    Used by endpoints that can function without ML models (e.g., placeholder mode).
    """
    return getattr(request.app.state, "text_inference", None)


def get_drift_monitor(request: Request) -> Optional[DriftMonitor]:
    """
    Get the drift monitor from app.state.
    Returns None if not initialized.
    """
    return getattr(request.app.state, "drift_monitor", None)


def get_image_model(request: Request):
    """
    FastAPI dependency to get the image prediction model.
    Returns None until Phase 2 (image pipeline).
    """
    return getattr(request.app.state, "image_model", None)


def get_meta_model(request: Request):
    """
    FastAPI dependency to get the meta-model (stacking) for credibility score.
    Returns None until meta-model is trained.
    """
    return getattr(request.app.state, "meta_model", None)
