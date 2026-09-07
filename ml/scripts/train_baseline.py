"""
Train the TruthLens baseline text model (TF-IDF + Logistic Regression).

This is a convenience wrapper around ml/training/text/train_baseline.py that:
1. Checks for ISOT dataset (downloads if missing)
2. Runs training with sensible defaults (fewer Optuna trials for speed)
3. Prints a clear summary at the end

Usage:
    python ml/scripts/train_baseline.py
    python ml/scripts/train_baseline.py --optuna-trials 30  # More trials = better model
"""

import os
import sys
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("truthlens.train")

# Add project root to path so ml.training.* imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)

DATA_DIR = os.path.join(PROJECT_ROOT, "ml", "data")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

from ml.training.utils.model_versions import validate_text_model_version


def validate_training_version(version: str) -> None:
    validate_text_model_version(version)


def ensure_dataset():
    """Download ISOT dataset if not already present."""
    true_path = os.path.join(DATA_DIR, "isot", "True.csv")
    fake_path = os.path.join(DATA_DIR, "isot", "Fake.csv")

    if not os.path.exists(true_path) or not os.path.exists(fake_path):
        logger.info("ISOT dataset not found. Downloading via Hugging Face Datasets...")
        from ml.scripts.download_data import download_isot
        download_isot(DATA_DIR)
    else:
        logger.info("ISOT dataset found. Skipping download.")


def main():
    parser = argparse.ArgumentParser(description="Train TruthLens baseline text model")
    parser.add_argument(
        "--optuna-trials",
        type=int,
        default=15,
        help="Number of Optuna hyperparameter tuning trials (default: 15, use 30 for best quality)",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="New model version string (for example: v1.3.0)",
    )
    args = parser.parse_args()
    validate_training_version(args.version)

    logger.info("=" * 60)
    logger.info("TruthLens Baseline Model Training")
    logger.info(f"  Version: {args.version}")
    logger.info(f"  Optuna trials: {args.optuna_trials}")
    logger.info(f"  Output: {MODELS_DIR}/text/{args.version}/")
    logger.info("=" * 60)

    # Step 1: Ensure dataset is available
    ensure_dataset()

    # Step 2: Run training
    from ml.training.text.train_baseline import train_baseline
    pipeline, metrics = train_baseline(
        n_optuna_trials=args.optuna_trials,
        version=args.version,
    )

    # Step 3: Print summary
    model_path = os.path.join(MODELS_DIR, "text", args.version, "model.pkl")
    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info(f"  Model saved: {model_path}")
    logger.info(f"  Test Accuracy: {metrics.get('accuracy', 0):.4f}")
    logger.info(f"  Test F1:       {metrics.get('f1', 0):.4f}")
    logger.info(f"  Test ROC-AUC:  {metrics.get('roc_auc', 0):.4f}")

    ood = metrics.get("ood_liar")
    if ood:
        logger.info(f"  OOD F1 (LIAR): {ood.get('f1', 0):.4f}")

    logger.info("=" * 60)
    logger.info("Next step: Upload model to Hugging Face Hub")
    logger.info("  python ml/scripts/upload_model.py")


if __name__ == "__main__":
    main()
