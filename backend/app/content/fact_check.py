"""Server-side lookup for already-published ClaimReview fact checks."""

import logging
import hashlib
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("truthlens.fact_check")
CLAIM_SEARCH_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
FACT_CHECK_CACHE_TTL_SECONDS = 3600
FACT_CHECK_CACHE_MAX_ENTRIES = 128
FACT_CHECK_MAX_COOLDOWN_SECONDS = 900
_cache: dict[str, tuple[float, dict[str, str]]] = {}
_cooldown_until = 0.0


def parse_claim_search_response(payload: dict[str, Any]) -> dict[str, str]:
    """Return one published review, or a safe no-match result."""
    for claim in payload.get("claims", []):
        for review in claim.get("claimReview", []):
            return {
                "status": "matched",
                "claim": claim.get("text", ""),
                "rating": review.get("textualRating", "Unrated"),
                "publisher": review.get("publisher", {}).get("name", "Unknown"),
                "url": review.get("url", ""),
            }
    return {"status": "not_found"}


async def search_fact_checks(text: str) -> dict[str, str]:
    """Search existing reviews; never infer a verdict if Google has no match."""
    global _cooldown_until

    if not settings.FACT_CHECK_API_KEY:
        return {"status": "unavailable"}

    now = time.monotonic()
    if now < _cooldown_until:
        return {"status": "unavailable"}

    cache_key = hashlib.sha256(text[:1000].encode()).hexdigest()
    cached = _cache.get(cache_key)
    if cached and now < cached[0]:
        return dict(cached[1])

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                CLAIM_SEARCH_URL,
                params={
                    "key": settings.FACT_CHECK_API_KEY,
                    "query": text[:1000],
                    "languageCode": "en",
                    "pageSize": 1,
                },
            )
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "")
                try:
                    cooldown = min(int(retry_after), FACT_CHECK_MAX_COOLDOWN_SECONDS)
                except ValueError:
                    cooldown = FACT_CHECK_MAX_COOLDOWN_SECONDS
                _cooldown_until = now + max(cooldown, 1)
                logger.warning("Fact-check lookup rate limited")
                return {"status": "unavailable"}
            response.raise_for_status()
        result = parse_claim_search_response(response.json())
        if len(_cache) >= FACT_CHECK_CACHE_MAX_ENTRIES:
            _cache.pop(next(iter(_cache)))
        _cache[cache_key] = (now + FACT_CHECK_CACHE_TTL_SECONDS, result)
        return result
    except httpx.HTTPError:
        logger.warning("Fact-check lookup unavailable")
        return {"status": "unavailable"}
