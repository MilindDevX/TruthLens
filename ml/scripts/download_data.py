"""
Download ISOT Fake News Dataset via Hugging Face Datasets.

The ISOT dataset is mirrored on HuggingFace as 'GonzaloA/fake_news',
which has the same True/Fake binary structure as the original ISOT CSVs.
This avoids needing a Kaggle account or manual CSV downloads.

Usage:
    python ml/scripts/download_data.py
    python ml/scripts/download_data.py --data-dir /path/to/data
"""

import os
import sys
import argparse
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("truthlens.download_data")

# Project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# data_loader.py resolves DATA_DIR as ml/data/ (3 levels up from ml/training/utils/)
# so we must save here too
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "ml", "data")
SOURCE_LABEL_MAPPING = {"0": "fake", "1": "real"}
TRAINING_LABEL_MAPPING = {"0": "real", "1": "fake"}


def split_labelled_articles(frame):
    """Return Hugging Face label 1 articles as real and label 0 articles as fake."""
    return frame[frame["label"] == 1].copy(), frame[frame["label"] == 0].copy()


def require_dataset_provenance(data_dir: str) -> dict:
    """Return a verified dataset manifest or reject legacy cached CSVs."""
    manifest_path = os.path.join(data_dir, "dataset_provenance.json")
    try:
        with open(manifest_path) as file:
            manifest = json.load(file)
    except FileNotFoundError as error:
        raise ValueError("dataset_provenance.json is required for cached training data.") from error

    if manifest.get("source_label_mapping") != SOURCE_LABEL_MAPPING:
        raise ValueError("dataset_provenance.json has an unexpected label mapping.")

    return manifest


def download_isot(data_dir: str) -> None:
    """
    Download and save the ISOT dataset (GonzaloA/fake_news on HuggingFace)
    as True.csv and Fake.csv into data/isot/ — matching the format
    expected by ml/training/utils/data_loader.py.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("datasets library not installed. Run: pip install datasets")
        sys.exit(1)

    import pandas as pd

    isot_dir = os.path.join(data_dir, "isot")
    os.makedirs(isot_dir, exist_ok=True)

    true_path = os.path.join(isot_dir, "True.csv")
    fake_path = os.path.join(isot_dir, "Fake.csv")

    if os.path.exists(true_path) and os.path.exists(fake_path):
        true_size = os.path.getsize(true_path)
        fake_size = os.path.getsize(fake_path)
        if true_size > 100_000 and fake_size > 100_000:
            try:
                require_dataset_provenance(isot_dir)
                logger.info(f"ISOT dataset already present at {isot_dir}, skipping download.")
                return
            except ValueError:
                logger.warning("Cached ISOT data lacks verified provenance; downloading fresh data.")

    logger.info("Downloading GonzaloA/fake_news from Hugging Face Datasets...")
    # GonzaloA/fake_news labels 0 as fake and 1 as real.
    dataset = load_dataset("GonzaloA/fake_news", trust_remote_code=True)

    # Combine all splits
    dfs = []
    for split in dataset:
        df = dataset[split].to_pandas()
        dfs.append(df)

    full_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total records: {len(full_df)}, columns: {list(full_df.columns)}")

    real_df, fake_df = split_labelled_articles(full_df)

    logger.info(f"Real articles: {len(real_df)}, Fake articles: {len(fake_df)}")

    # Save in ISOT format (True.csv / Fake.csv)
    # Ensure required columns exist
    for df in [real_df, fake_df]:
        if "title" not in df.columns:
            df["title"] = ""
        if "text" not in df.columns:
            df["text"] = df.get("content", "")
        if "subject" not in df.columns:
            df["subject"] = "unknown"
        if "date" not in df.columns:
            df["date"] = ""

    real_df[["title", "text", "subject", "date"]].to_csv(true_path, index=False)
    fake_df[["title", "text", "subject", "date"]].to_csv(fake_path, index=False)
    with open(os.path.join(isot_dir, "dataset_provenance.json"), "w") as file:
        json.dump(
            {
                "dataset": "GonzaloA/fake_news",
                "fingerprints": {
                    split: getattr(dataset[split], "_fingerprint", None)
                    for split in dataset
                },
                "source_label_mapping": SOURCE_LABEL_MAPPING,
                "training_label_mapping": TRAINING_LABEL_MAPPING,
            },
            file,
            indent=2,
        )

    logger.info(f"Saved True.csv ({len(real_df)} rows) to {true_path}")
    logger.info(f"Saved Fake.csv ({len(fake_df)} rows) to {fake_path}")
    logger.info("ISOT dataset download complete.")


def main():
    parser = argparse.ArgumentParser(description="Download TruthLens training datasets")
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help=f"Directory to save datasets (default: {DEFAULT_DATA_DIR})",
    )
    args = parser.parse_args()

    logger.info(f"Data directory: {args.data_dir}")
    download_isot(args.data_dir)


if __name__ == "__main__":
    main()
