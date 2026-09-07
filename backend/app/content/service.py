"""
Content analysis service layer.
Orchestrates: validation → dedup check → inference → explainability → history storage.
Routers NEVER call inference/DB directly — only through this service.
"""

import time
import logging
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Request

from app.content.validators import validate_text_input, compute_content_hash
from app.content.schemas import (
    AnalysisResponse, ModelScore, ExplainabilityData, FactCheckResult, TokenImpact,
)
from app.content.fact_check import search_fact_checks
from app.history.models import AnalysisHistory
from app.ml.text_inference import TextInferenceService

logger = logging.getLogger("truthlens.content")


def select_final_model(prediction_result: dict) -> dict:
    """Use the advanced score only when an advanced model actually returned one."""
    return prediction_result.get("advanced", prediction_result["baseline"])


async def analyze_text(
    db: AsyncSession,
    text: str,
    user_id: UUID,
    request: Request,
    inference_service: TextInferenceService,
) -> AnalysisResponse:
    """
    Full text analysis pipeline:
    1. Validate and sanitize input
    2. Check content dedup cache (SHA-256)
    3. Run inference (baseline + advanced) via TextInferenceService
    4. Compute estimated P(real)
    5. Generate available explainability data
    6. Record drift stats
    7. Save to history
    8. Return structured response with timing

    Uses request.state.timing for perf logging.
    """
    # Step 1: Validate
    preprocess_start = time.perf_counter()
    clean_text = validate_text_input(text)
    content_hash = compute_content_hash(clean_text)
    preprocess_ms = round((time.perf_counter() - preprocess_start) * 1000, 2)

    # Step 2: Dedup check — return cached result if identical content was analyzed before
    cached = await _check_dedup_cache(db, content_hash, user_id)
    if cached:
        request.state.timing["preprocessing_ms"] = preprocess_ms
        request.state.timing["inference_ms"] = 0
        request.state.timing["cache_hit"] = True
        return cached.model_copy(
            update={"fact_check": FactCheckResult(**await search_fact_checks(clean_text))}
        )

    # Step 3: Run inference
    inference_start = time.perf_counter()

    prediction_result = await inference_service.predict(clean_text)
    model_version = inference_service.version
    fact_check = FactCheckResult(**await search_fact_checks(clean_text))

    inference_ms = round((time.perf_counter() - inference_start) * 1000, 2)

    # Step 4: Explainability
    explain_start = time.perf_counter()

    explain_result = await inference_service.explain(clean_text)
    explainability = ExplainabilityData(
        type=explain_result.get("type", "none"),
        influential_tokens=[
            TokenImpact(**t) for t in explain_result.get("influential_tokens", [])
        ],
    )

    explain_ms = round((time.perf_counter() - explain_start) * 1000, 2)

    # Step 5: Build model scores
    model_scores = {
        "baseline": ModelScore(
            prediction=prediction_result["baseline"]["prediction"],
            confidence=prediction_result["baseline"]["confidence"],
        ),
    }
    if "advanced" in prediction_result:
        model_scores["advanced"] = ModelScore(
            prediction=prediction_result["advanced"]["prediction"],
            confidence=prediction_result["advanced"]["confidence"],
        )

    final_model = select_final_model(prediction_result)
    final_prediction = final_model["prediction"]
    final_confidence = final_model["confidence"]

    # Step 6: P(real), derived directly from the selected model's P(fake).
    credibility_score = round(1 - final_model["probability"], 4)

    # Step 7: Flag probabilities near the decision boundary.
    low_confidence = 0.4 <= final_model["probability"] <= 0.6

    # Step 8: Record drift stats
    drift_monitor = getattr(request.app.state, "drift_monitor", None)
    if drift_monitor is not None:
        pred_int = 1 if final_prediction == "fake" else 0
        drift_monitor.record(final_confidence, pred_int)

    # Step 9: Save to history
    history_record = AnalysisHistory(
        user_id=user_id,
        content_type="text",
        content_hash=content_hash,
        input_preview=clean_text[:200],
        prediction=final_prediction,
        confidence_score=final_confidence,
        credibility_score=credibility_score,
        model_scores={k: v.model_dump() for k, v in model_scores.items()},
        explainability_data=explainability.model_dump() if explainability else None,
        model_version=model_version,
        low_confidence_flag=low_confidence,
    )
    db.add(history_record)
    await db.flush()

    # Step 10: Update timing for logging middleware
    # Merge in per-stage timings from TextInferenceService
    timings = prediction_result.get("timings")
    request.state.timing["preprocessing_ms"] = preprocess_ms
    request.state.timing["inference_ms"] = inference_ms
    request.state.timing["explainability_ms"] = explain_ms
    if timings is not None:
        request.state.timing["baseline_ms"] = timings.baseline_ms
        request.state.timing["advanced_ms"] = timings.advanced_ms

    return AnalysisResponse(
        id=history_record.id,
        content_type="text",
        prediction=final_prediction,
        confidence=final_confidence,
        low_confidence_flag=low_confidence,
        model_scores=model_scores,
        credibility_score=credibility_score,
        explainability=explainability,
        fact_check=fact_check,
        model_version=model_version,
        created_at=history_record.created_at,
    )


async def fact_check_text(text: str) -> FactCheckResult:
    """Look up published fact checks without relying on a local classifier."""
    clean_text = validate_text_input(text)
    return FactCheckResult(**await search_fact_checks(clean_text))


async def _check_dedup_cache(
    db: AsyncSession,
    content_hash: str,
    user_id: UUID,
) -> Optional[AnalysisResponse]:
    """
    Check if identical content has been analyzed before by this user.
    Returns cached AnalysisResponse if found, None otherwise.
    """
    result = await db.execute(
        select(AnalysisHistory)
        .where(
            AnalysisHistory.content_hash == content_hash,
            AnalysisHistory.user_id == user_id,
        )
        .order_by(AnalysisHistory.created_at.desc())
        .limit(1)
    )
    cached = result.scalar_one_or_none()

    if cached is None:
        return None

    # Reconstruct response from cached record
    model_scores = {}
    if cached.model_scores:
        for k, v in cached.model_scores.items():
            model_scores[k] = ModelScore(**v)

    explainability = None
    if cached.explainability_data:
        explainability = ExplainabilityData(**cached.explainability_data)

    return AnalysisResponse(
        id=cached.id,
        content_type=cached.content_type,
        prediction=cached.prediction,
        confidence=cached.confidence_score,
        low_confidence_flag=cached.low_confidence_flag,
        model_scores=model_scores,
        credibility_score=cached.credibility_score,
        explainability=explainability,
        model_version=cached.model_version,
        created_at=cached.created_at,
    )
