import inspect
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest

from app.content import fact_check
from app.content import service
from app.content.fact_check import parse_claim_search_response
from app.content.router import fact_check_text_endpoint
from app.content.schemas import AnalysisResponse


def test_parses_the_first_fact_check_review():
    result = parse_claim_search_response(
        {
            "claims": [
                {
                    "text": "A claim",
                    "claimReview": [
                        {
                            "textualRating": "False",
                            "publisher": {"name": "FactCheck.org"},
                            "url": "https://example.com/review",
                        }
                    ],
                }
            ]
        }
    )

    assert result == {
        "status": "matched",
        "claim": "A claim",
        "rating": "False",
        "publisher": "FactCheck.org",
        "url": "https://example.com/review",
    }


def test_returns_not_found_for_an_empty_claim_response():
    assert parse_claim_search_response({"claims": []}) == {"status": "not_found"}


def test_fact_check_route_does_not_depend_on_a_text_model():
    parameters = inspect.signature(fact_check_text_endpoint).parameters

    assert "inference_service" not in parameters
    assert "db" not in parameters


class FakeResponse:
    def __init__(self, payload, status_code=200, headers=None):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("failed", request=None, response=self)


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def get(self, *_args, **_kwargs):
        self.calls += 1
        return self.response


@pytest.fixture(autouse=True)
def reset_fact_check_state(monkeypatch):
    monkeypatch.setattr(fact_check, "_cache", {}, raising=False)
    monkeypatch.setattr(fact_check, "_cooldown_until", 0, raising=False)
    monkeypatch.setattr(fact_check.settings, "FACT_CHECK_API_KEY", "test-key")


@pytest.mark.asyncio
async def test_reuses_a_cached_claim_lookup(monkeypatch):
    client = FakeClient(FakeResponse({"claims": []}))
    monkeypatch.setattr(fact_check.httpx, "AsyncClient", lambda **_kwargs: client)

    assert await fact_check.search_fact_checks("The claim") == {"status": "not_found"}
    assert await fact_check.search_fact_checks("The claim") == {"status": "not_found"}
    assert client.calls == 1


@pytest.mark.asyncio
async def test_stops_calling_google_during_a_rate_limit_cooldown(monkeypatch):
    client = FakeClient(FakeResponse({}, status_code=429, headers={"Retry-After": "60"}))
    monkeypatch.setattr(fact_check.httpx, "AsyncClient", lambda **_kwargs: client)

    assert await fact_check.search_fact_checks("First claim") == {"status": "unavailable"}
    assert await fact_check.search_fact_checks("Second claim") == {"status": "unavailable"}
    assert client.calls == 1


@pytest.mark.asyncio
async def test_cached_analysis_still_includes_external_evidence(monkeypatch):
    cached = AnalysisResponse(
        id=uuid4(),
        content_type="text",
        prediction="real",
        confidence=0.8,
        low_confidence_flag=False,
        model_scores={},
        credibility_score=0.8,
        model_version="v1.1.0",
        created_at=datetime.now(timezone.utc),
    )
    lookup = AsyncMock(return_value={"status": "not_found"})
    monkeypatch.setattr(service, "_check_dedup_cache", AsyncMock(return_value=cached))
    monkeypatch.setattr(service, "search_fact_checks", lookup)
    request = SimpleNamespace(state=SimpleNamespace(timing={}))

    result = await service.analyze_text(
        db=None,
        text="Cached text",
        user_id=uuid4(),
        request=request,
        inference_service=None,
    )

    assert result.fact_check.status == "not_found"
    assert result.evidence_priority == "model_estimate"
    lookup.assert_awaited_once_with("Cached text")


@pytest.mark.asyncio
async def test_cached_analysis_marks_a_matched_review_as_primary_evidence(monkeypatch):
    cached = AnalysisResponse(
        id=uuid4(), content_type="text", prediction="real", confidence=0.8,
        low_confidence_flag=False, model_scores={}, credibility_score=0.8,
        model_version="v1.3.0", created_at=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(service, "_check_dedup_cache", AsyncMock(return_value=cached))
    monkeypatch.setattr(service, "search_fact_checks", AsyncMock(return_value={
        "status": "matched", "publisher": "FactCheck.org", "rating": "False",
    }))
    request = SimpleNamespace(state=SimpleNamespace(timing={}))

    result = await service.analyze_text(
        db=None, text="Cached text", user_id=uuid4(), request=request, inference_service=None,
    )

    assert result.evidence_priority == "published_fact_check"


def test_analysis_response_defaults_to_a_secondary_model_estimate():
    response = AnalysisResponse(
        id=uuid4(), content_type="text", prediction="real", confidence=0.8,
        low_confidence_flag=False, model_scores={}, credibility_score=0.8,
        model_version="v1.3.0", created_at=datetime.now(timezone.utc),
    )

    assert response.evidence_priority == "model_estimate"
