"""
Version-aware model loader.
Loads trained models from versioned filesystem into TextInferenceService.

Supports:
- Baseline: joblib Pipeline (TF-IDF + LR) → model.pkl
- Advanced: DistilBERT state_dict + tokenizer → model.pt + tokenizer/
- Atomic reload: create new service → swap on app.state → release old ref
"""

import os
import json
import logging
import joblib
from typing import Optional

from app.config import settings
from app.ml.text_inference import TextInferenceService
from app.ml.drift_monitor import DriftMonitor

logger = logging.getLogger("truthlens.model_loader")


def get_model_path(model_type: str, version: Optional[str] = None) -> str:
    """
    Get the filesystem path for a model version.

    Args:
        model_type: "text" or "image"
        version: Semantic version (e.g., "v1.0.0"). Uses active version from config if None.

    Returns:
        Absolute path to the model version directory.
    """
    if version is None:
        version = (
            settings.ACTIVE_TEXT_MODEL_VERSION
            if model_type == "text"
            else settings.ACTIVE_IMAGE_MODEL_VERSION
        )
    return os.path.join(settings.MODELS_DIR, model_type, version)


def load_model_metadata(model_type: str, version: Optional[str] = None) -> dict:
    """Load metadata.json for a given model version."""
    model_path = get_model_path(model_type, version)
    metadata_path = os.path.join(model_path, "metadata.json")

    if not os.path.exists(metadata_path):
        logger.warning(f"No metadata found at {metadata_path}")
        return {}

    with open(metadata_path, "r") as f:
        return json.load(f)


def get_latest_version(model_type: str) -> Optional[str]:
    """
    Find the latest model version by scanning the model directory.
    Versions follow semantic versioning (v1.0.0).
    """
    model_dir = os.path.join(settings.MODELS_DIR, model_type)
    if not os.path.exists(model_dir):
        return None

    versions = [
        d for d in os.listdir(model_dir)
        if os.path.isdir(os.path.join(model_dir, d)) and d.startswith("v")
    ]

    if not versions:
        return None

    # Sort by semantic version (filter out suffixed versions like v1.0.0_advanced)
    base_versions = [v for v in versions if "_" not in v]
    if not base_versions:
        base_versions = versions

    base_versions.sort(key=lambda v: [int(x) for x in v.lstrip("v").split("_")[0].split(".")])
    return base_versions[-1]


def _load_baseline(version: str):
    """Load baseline TF-IDF+LR pipeline from joblib."""
    model_path = os.path.join(settings.MODELS_DIR, "text", version, "model.pkl")

    if not os.path.exists(model_path):
        logger.warning(f"Baseline model not found at {model_path}")
        return None

    logger.info(f"Loading baseline model from {model_path}")
    pipeline = joblib.load(model_path)
    logger.info(f"Baseline model loaded successfully ({type(pipeline).__name__})")
    return pipeline


def _load_advanced(version: str):
    """Load DistilBERT model and tokenizer from torch checkpoint."""
    advanced_dir = os.path.join(settings.MODELS_DIR, "text", f"{version}_advanced")
    model_path = os.path.join(advanced_dir, "model.pt")
    tokenizer_path = os.path.join(advanced_dir, "tokenizer")

    if not os.path.exists(model_path):
        logger.warning(f"Advanced model not found at {model_path}")
        return None, None

    if not os.path.exists(tokenizer_path):
        logger.warning(f"Advanced tokenizer not found at {tokenizer_path}")
        return None, None

    try:
        import torch
        from transformers import DistilBertForSequenceClassification, DistilBertTokenizer

        logger.info(f"Loading advanced model from {advanced_dir}")

        tokenizer = DistilBertTokenizer.from_pretrained(tokenizer_path)
        model = DistilBertForSequenceClassification.from_pretrained(
            "distilbert-base-uncased", num_labels=2
        )
        model.load_state_dict(
            torch.load(model_path, map_location=torch.device("cpu"), weights_only=True)
        )
        model.eval()

        logger.info("Advanced model loaded successfully (DistilBERT)")
        return model, tokenizer

    except ImportError:
        logger.warning("PyTorch/transformers not installed — skipping advanced model")
        return None, None
    except Exception as e:
        logger.error(f"Failed to load advanced model: {e}", exc_info=True)
        return None, None


def _build_inference_service(version: str) -> TextInferenceService:
    """
    Build a TextInferenceService with whatever models are available.

    - Loads baseline (joblib) — fast, always attempted
    - Loads advanced (DistilBERT) — heavier, graceful fallback if missing
    - Loads metadata for version info
    """
    baseline_pipeline = _load_baseline(version)
    advanced_model, advanced_tokenizer = _load_advanced(version)
    metadata = load_model_metadata("text", version)

    if baseline_pipeline is None and advanced_model is None:
        logger.warning(
            f"No text models found for version {version}. "
            "Running in placeholder mode — predictions will be empty."
        )

    return TextInferenceService(
        baseline_pipeline=baseline_pipeline,
        advanced_model=advanced_model,
        advanced_tokenizer=advanced_tokenizer,
        version=version,
        metadata=metadata,
    )


async def load_text_model(app_state) -> None:
    """
    Load text models into app.state at startup.

    Creates:
    - app.state.text_inference: TextInferenceService instance
    - app.state.text_model_version: active version string
    - app.state.drift_monitor: DriftMonitor instance
    """
    version = settings.ACTIVE_TEXT_MODEL_VERSION

    try:
        service = _build_inference_service(version)
        app_state.text_inference = service
        app_state.text_model_version = version
        app_state.text_model = service  # Backward compat with health check

        # Initialize drift monitor
        app_state.drift_monitor = DriftMonitor(window_size=1000)

        logger.info(
            f"Text inference ready: version={version}, "
            f"baseline={'✓' if service.has_baseline else '✗'}, "
            f"advanced={'✓' if service.has_advanced else '✗'}"
        )
    except Exception as e:
        logger.error(f"Failed to load text models: {e}", exc_info=True)
        app_state.text_inference = None
        app_state.text_model_version = None
        app_state.text_model = None
        app_state.drift_monitor = DriftMonitor(window_size=1000)


async def reload_text_model(
    app_state,
    version: Optional[str] = None,
) -> dict:
    """
    Atomic model reload for admin endpoint.

    1. Build new TextInferenceService from disk
    2. Swap reference on app.state (atomic pointer swap)
    3. Reset drift monitor
    4. Old service objects become garbage-collectible

    Args:
        app_state: FastAPI app.state
        version: Version to load (defaults to latest available)

    Returns:
        dict with status, version, and capabilities
    """
    if version is None:
        version = get_latest_version("text") or settings.ACTIVE_TEXT_MODEL_VERSION

    logger.info(f"Reloading text model to version {version}...")

    new_service = _build_inference_service(version)

    # Atomic swap (Python reference assignment is atomic)
    old_service = getattr(app_state, "text_inference", None)
    app_state.text_inference = new_service
    app_state.text_model_version = version
    app_state.text_model = new_service  # Backward compat

    # Reset drift monitor for new model
    drift_monitor = getattr(app_state, "drift_monitor", None)
    if drift_monitor:
        drift_monitor.reset()

    # Old service will be garbage collected
    del old_service

    logger.info(
        f"Text model reloaded: version={version}, "
        f"baseline={'✓' if new_service.has_baseline else '✗'}, "
        f"advanced={'✓' if new_service.has_advanced else '✗'}"
    )

    return {
        "version": version,
        "has_baseline": new_service.has_baseline,
        "has_advanced": new_service.has_advanced,
        "metadata": new_service.metadata,
    }


async def load_image_model(app_state) -> None:
    """Placeholder for Phase 2 image pipeline."""
    app_state.image_model = None
    app_state.image_model_version = None


async def load_meta_model(app_state) -> None:
    """Placeholder for meta-model (stacking)."""
    app_state.meta_model = None
    app_state.meta_model_version = None
