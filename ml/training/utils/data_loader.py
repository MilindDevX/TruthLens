"""
Dataset loading, splitting, and preprocessing utilities.
Handles ISOT and LIAR datasets with group-based stratified splitting.
"""

import os
import hashlib
import logging
import pandas as pd
import numpy as np
from typing import Optional
from sklearn.model_selection import StratifiedGroupKFold, train_test_split

logger = logging.getLogger("truthlens.ml.data_loader")

# Path to local data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def load_isot_dataset(data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load the ISOT Fake News Dataset (binary: Real/Fake).

    Expected files:
    - data/isot/True.csv (real news)
    - data/isot/Fake.csv (fake news)

    Returns DataFrame with columns: [text, title, label, source]
    where label: 0 = real, 1 = fake
    """
    data_path = data_dir or os.path.join(DATA_DIR, "isot")

    true_path = os.path.join(data_path, "True.csv")
    fake_path = os.path.join(data_path, "Fake.csv")

    if not os.path.exists(true_path) or not os.path.exists(fake_path):
        raise FileNotFoundError(
            f"ISOT dataset not found at {data_path}. "
            f"Please download True.csv and Fake.csv from: "
            f"https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset"
        )

    true_df = pd.read_csv(true_path)
    true_df["label"] = 0  # Real

    fake_df = pd.read_csv(fake_path)
    fake_df["label"] = 1  # Fake

    df = pd.concat([true_df, fake_df], ignore_index=True)

    # Extract source/publisher for group-based splitting
    if "subject" in df.columns:
        df["source"] = df["subject"]
    else:
        df["source"] = "unknown"

    # Combine title + text for full content
    df["full_text"] = df["title"].fillna("") + " " + df["text"].fillna("")

    # Dedup by content hash
    df["content_hash"] = df["full_text"].apply(
        lambda x: hashlib.sha256(x.encode()).hexdigest()
    )
    initial_size = len(df)
    df = df.drop_duplicates(subset=["content_hash"])
    deduped = initial_size - len(df)
    if deduped > 0:
        logger.info(f"Removed {deduped} duplicate articles from ISOT dataset")

    logger.info(
        f"ISOT dataset loaded: {len(df)} articles, "
        f"Real: {(df['label'] == 0).sum()}, Fake: {(df['label'] == 1).sum()}"
    )

    return df[["full_text", "title", "text", "label", "source", "content_hash"]]


def load_liar_dataset(data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load the LIAR dataset for out-of-distribution validation.

    LIAR has 6 classes which we map to binary:
    - real (0): true, mostly-true, half-true
    - fake (1): barely-true, false, pants-fire

    Expected file: data/liar/train.tsv (tab-separated)
    """
    data_path = data_dir or os.path.join(DATA_DIR, "liar")

    # LIAR column names
    columns = [
        "id", "label_original", "text", "subject", "speaker",
        "job_title", "state_info", "party", "barely_true_count",
        "false_count", "half_true_count", "mostly_true_count",
        "pants_on_fire_count", "context",
    ]

    dfs = []
    for split in ["train.tsv", "valid.tsv", "test.tsv"]:
        filepath = os.path.join(data_path, split)
        if os.path.exists(filepath):
            df = pd.read_csv(filepath, sep="\t", header=None, names=columns)
            dfs.append(df)

    if not dfs:
        raise FileNotFoundError(
            f"LIAR dataset not found at {data_path}. "
            f"Please download from: https://www.cs.ucsb.edu/~william/data/liar_dataset.zip"
        )

    df = pd.concat(dfs, ignore_index=True)

    # Map to binary
    real_labels = {"true", "mostly-true", "half-true"}
    df["label"] = df["label_original"].apply(lambda x: 0 if x in real_labels else 1)
    df["full_text"] = df["text"].fillna("")
    df["source"] = df["speaker"].fillna("unknown")

    logger.info(
        f"LIAR dataset loaded: {len(df)} statements, "
        f"Real: {(df['label'] == 0).sum()}, Fake: {(df['label'] == 1).sum()}"
    )

    return df[["full_text", "text", "label", "source"]]


def split_dataset(
    df: pd.DataFrame,
    test_size: float = 0.1,
    val_size: float = 0.1,
    random_state: int = 42,
    group_col: Optional[str] = "source",
    label_col: str = "label",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into train/val/test with stratification.

    If group_col is provided, uses group-based splitting to prevent
    source leakage (articles from same source don't appear in both train and test).

    Default: 80/10/10 split.

    Returns: (train_df, val_df, test_df)
    """
    if group_col and group_col in df.columns:
        # Group-based stratified split
        # First split off test set
        unique_groups = df[group_col].unique()
        n_groups = len(unique_groups)

        if n_groups > 5:
            # Use StratifiedGroupKFold for group-based splitting
            try:
                sgkf = StratifiedGroupKFold(n_splits=int(1 / test_size), shuffle=True, random_state=random_state)
                train_val_idx, test_idx = next(sgkf.split(df, df[label_col], df[group_col]))
                test_df = df.iloc[test_idx]
                train_val_df = df.iloc[train_val_idx]
            except ValueError:
                # Fall back to stratified split without groups
                logger.warning("Group-based split failed, falling back to stratified split")
                train_val_df, test_df = train_test_split(
                    df, test_size=test_size, stratify=df[label_col], random_state=random_state
                )
        else:
            # Too few groups for group-based splitting
            train_val_df, test_df = train_test_split(
                df, test_size=test_size, stratify=df[label_col], random_state=random_state
            )
    else:
        train_val_df, test_df = train_test_split(
            df, test_size=test_size, stratify=df[label_col], random_state=random_state
        )

    # Split train_val into train and val
    relative_val_size = val_size / (1 - test_size)
    train_df, val_df = train_test_split(
        train_val_df, test_size=relative_val_size,
        stratify=train_val_df[label_col], random_state=random_state,
    )

    logger.info(
        f"Dataset split: train={len(train_df)}, val={len(val_df)}, test={len(test_df)} "
        f"(ratios: {len(train_df)/len(df):.2f}/{len(val_df)/len(df):.2f}/{len(test_df)/len(df):.2f})"
    )

    # Log label distribution per split
    for name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        dist = split_df[label_col].value_counts(normalize=True)
        logger.info(f"  {name}: {dict(dist.round(3))}")

    return train_df, val_df, test_df
