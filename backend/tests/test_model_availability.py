from types import SimpleNamespace
import inspect

import pytest
from fastapi import HTTPException

from app.content.router import analyze_text_endpoint
from app.content import service
from app.main import app, health_check
from app.ml import model_loader
from app.ml.dependencies import get_text_inference


def request_for(service):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(text_inference=service)))


def test_requires_a_loaded_baseline():
    with pytest.raises(HTTPException) as error:
        get_text_inference(request_for(SimpleNamespace(has_baseline=False)))

    assert error.value.status_code == 503
    assert error.value.detail == "Text model unavailable. Try again later."


def test_returns_loaded_baseline_service():
    service = SimpleNamespace(has_baseline=True)

    assert get_text_inference(request_for(service)) is service


def test_analysis_route_requires_loaded_model_service():
    dependency = inspect.signature(analyze_text_endpoint).parameters[
        "inference_service"
    ].default.dependency

    assert dependency is get_text_inference


def test_baseline_is_final_model_when_advanced_model_is_absent():
    baseline = {"prediction": "fake", "confidence": 0.9, "probability": 0.9}

    assert service.select_final_model({"baseline": baseline}) is baseline


@pytest.mark.parametrize("version", ["v1.0.0", "v1.1.0", "v1.2.0"])
def test_rejects_invalid_or_failed_model_artifact_versions(version):
    with pytest.raises(ValueError, match=f"{version} is invalid"):
        model_loader.validate_text_model_version(version)


def test_rejects_model_metadata_without_verified_training_labels():
    with pytest.raises(ValueError, match="training label mapping"):
        model_loader.validate_text_model_metadata(
            {"training_label_mapping": {"0": "fake", "1": "real"}}
        )


def test_rejects_model_metadata_below_held_out_liar_gate():
    with pytest.raises(ValueError, match="held-out LIAR"):
        model_loader.validate_text_model_metadata(
            {
                "training_label_mapping": {"0": "real", "1": "fake"},
                "ood_validation": {"f1": 0.59},
            }
        )


def test_rejects_model_metadata_from_a_different_sklearn_runtime():
    with pytest.raises(ValueError, match="scikit-learn version"):
        model_loader.validate_text_model_metadata(
            {
                "training_label_mapping": {"0": "real", "1": "fake"},
                "ood_validation": {"f1": 0.8},
                "sklearn_version": "0.0.0",
            }
        )


@pytest.mark.asyncio
async def test_health_is_unavailable_without_baseline():
    app.state.text_inference = SimpleNamespace(
        version="v1.0.0", has_baseline=False, has_advanced=False
    )

    response = await health_check()

    assert response.status_code == 503
    assert b'"status":"unavailable"' in response.body


@pytest.mark.asyncio
async def test_health_is_healthy_with_baseline():
    app.state.text_inference = SimpleNamespace(
        version="v1.1.0", has_baseline=True, has_advanced=False
    )

    response = await health_check()

    assert response["status"] == "healthy"
    assert response["models"]["text"]["has_baseline"] is True
