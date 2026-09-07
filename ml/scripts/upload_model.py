"""
Upload trained TruthLens models to Hugging Face Hub.

Creates/updates a public model repository with:
- models/text/v1.0.0/model.pkl       (TF-IDF + LR baseline)
- models/text/v1.0.0/metadata.json   (training metadata)

Usage:
    # Login first (only needed once)
    huggingface-cli login

    # Upload
    python ml/scripts/upload_model.py --repo <username>/truthlens-models

    # Or set HF_REPO env var
    HF_REPO=<username>/truthlens-models python ml/scripts/upload_model.py
"""

import os
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("truthlens.upload")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

from ml.training.utils.model_versions import validate_text_model_version


def upload_models(repo_id: str, version: str = "v1.3.0") -> None:
    """Upload trained model files to Hugging Face Hub."""
    validate_text_model_version(version)
    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        logger.error("huggingface_hub not installed. Run: pip install huggingface_hub")
        sys.exit(1)

    model_dir = os.path.join(MODELS_DIR, "text", version)
    model_pkl = os.path.join(model_dir, "model.pkl")
    metadata_json = os.path.join(model_dir, "metadata.json")

    # Validate files exist
    for path in [model_pkl, metadata_json]:
        if not os.path.exists(path):
            logger.error(f"File not found: {path}")
            logger.error("Run training first: python ml/scripts/train_baseline.py")
            sys.exit(1)

    api = HfApi()

    # Create repo if it doesn't exist (public, model type)
    logger.info(f"Ensuring repository exists: {repo_id}")
    try:
        create_repo(repo_id=repo_id, repo_type="model", exist_ok=True, private=False)
        logger.info(f"Repository ready: https://huggingface.co/{repo_id}")
    except Exception as e:
        logger.warning(f"Could not create repo (may already exist): {e}")

    # Upload model.pkl
    logger.info(f"Uploading model.pkl ({os.path.getsize(model_pkl) / 1024 / 1024:.1f} MB)...")
    api.upload_file(
        path_or_fileobj=model_pkl,
        path_in_repo=f"models/text/{version}/model.pkl",
        repo_id=repo_id,
        repo_type="model",
        commit_message=f"Add baseline model {version}",
    )

    # Upload metadata.json
    logger.info("Uploading metadata.json...")
    api.upload_file(
        path_or_fileobj=metadata_json,
        path_in_repo=f"models/text/{version}/metadata.json",
        repo_id=repo_id,
        repo_type="model",
        commit_message=f"Add model metadata {version}",
    )

    logger.info("=" * 60)
    logger.info("UPLOAD COMPLETE")
    logger.info(f"  Repository: https://huggingface.co/{repo_id}")
    logger.info(f"  model.pkl:  models/text/{version}/model.pkl")
    logger.info(f"  metadata:   models/text/{version}/metadata.json")
    logger.info("")
    logger.info("Next step: Set HF_MODEL_REPO env var on Render:")
    logger.info(f"  HF_MODEL_REPO={repo_id}")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Upload TruthLens models to Hugging Face Hub")
    parser.add_argument(
        "--repo",
        default=os.environ.get("HF_REPO", ""),
        help="Hugging Face repo ID (e.g. yourname/truthlens-models). "
             "Can also set HF_REPO env var.",
    )
    parser.add_argument(
        "--version",
        default="v1.3.0",
        help="Model version to upload (default: v1.3.0)",
    )
    args = parser.parse_args()

    if not args.repo:
        logger.error("--repo is required. Example: --repo yourname/truthlens-models")
        logger.error("Or set HF_REPO environment variable.")
        sys.exit(1)

    upload_models(repo_id=args.repo, version=args.version)


if __name__ == "__main__":
    main()
