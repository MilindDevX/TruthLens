"""
Backend startup script: download ML models from Hugging Face Hub.

This script runs once when the container starts (before gunicorn).
It is idempotent: if models are already present, it skips downloading.

Environment variables:
    HF_MODEL_REPO  - Hugging Face repo ID (e.g. "yourname/truthlens-models")
                     If not set, script exits silently (placeholder mode).

Usage (in Dockerfile CMD):
    python /app/scripts/download_models.py && gunicorn app.main:app -c gunicorn.conf.py
"""

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("truthlens.startup.models")

DEFAULT_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
    "models"
)
MODELS_DIR = os.environ.get("MODELS_DIR", DEFAULT_MODELS_DIR)
HF_MODEL_REPO = os.environ.get("HF_MODEL_REPO", "")
MODEL_VERSION = os.environ.get("ACTIVE_TEXT_MODEL_VERSION", "v1.0.0")


def models_already_present(version: str) -> bool:
    """Return True if baseline model file already exists."""
    model_pkl = os.path.join(MODELS_DIR, "text", version, "model.pkl")
    return os.path.exists(model_pkl)


def download_from_hf(repo_id: str, version: str) -> bool:
    """
    Download model files from Hugging Face Hub.
    Returns True on success, False on failure.
    """
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        logger.warning("huggingface_hub not installed — running in placeholder mode")
        return False

    target_dir = os.path.join(MODELS_DIR, "text", version)
    os.makedirs(target_dir, exist_ok=True)

    files_to_download = [
        (f"models/text/{version}/model.pkl", os.path.join(target_dir, "model.pkl")),
        (f"models/text/{version}/metadata.json", os.path.join(target_dir, "metadata.json")),
    ]

    for repo_path, local_path in files_to_download:
        if os.path.exists(local_path):
            logger.info(f"  Already exists: {local_path} — skipping")
            continue

        logger.info(f"  Downloading {repo_path} from {repo_id}...")
        try:
            import shutil, tempfile
            # Download to a temp cache dir to avoid path nesting issues
            with tempfile.TemporaryDirectory() as tmp_dir:
                downloaded = hf_hub_download(
                    repo_id=repo_id,
                    filename=repo_path,
                    repo_type="model",
                    local_dir=tmp_dir,
                    local_dir_use_symlinks=False,
                )
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                shutil.copy2(downloaded, local_path)
                logger.info(f"  Saved to: {local_path}")
        except Exception as e:
            logger.error(f"  Failed to download {repo_path}: {e}")
            return False

    return True



def main():
    if not HF_MODEL_REPO:
        logger.info(
            "HF_MODEL_REPO not set — skipping model download (running in placeholder mode).\n"
            "Set HF_MODEL_REPO=<username>/truthlens-models on Render to enable real ML."
        )
        sys.exit(0)

    logger.info(f"Model download check — repo: {HF_MODEL_REPO}, version: {MODEL_VERSION}")

    if models_already_present(MODEL_VERSION):
        logger.info(f"Models already present for {MODEL_VERSION}. No download needed.")
        sys.exit(0)

    logger.info(f"Downloading models from {HF_MODEL_REPO}...")
    success = download_from_hf(HF_MODEL_REPO, MODEL_VERSION)

    if success and models_already_present(MODEL_VERSION):
        logger.info("Model download complete. Backend will use real ML inference.")
        sys.exit(0)
    else:
        logger.warning(
            "Model download failed or model.pkl not found. "
            "Backend will start in placeholder mode."
        )
        # Exit 0 so gunicorn still starts — we degrade gracefully
        sys.exit(0)


if __name__ == "__main__":
    main()
