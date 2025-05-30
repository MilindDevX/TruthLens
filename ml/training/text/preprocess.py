"""
Text preprocessing pipeline for TruthLens X.

Steps:
1. Lowercase
2. Remove URLs, emails, special characters
3. Remove duplicates (by content hash — done in data_loader)
4. For baseline: stopword removal + lemmatization
5. For advanced: tokenization handled by DistilBERT tokenizer (minimal preprocessing)
"""

import re
import logging
import nltk
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("truthlens.ml.preprocess")

# Ensure NLTK data is available
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet", quiet=True)

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

STOP_WORDS = set(stopwords.words("english"))
LEMMATIZER = WordNetLemmatizer()


def clean_text(text: str) -> str:
    """
    Basic text cleaning applied to ALL models:
    - Lowercase
    - Remove URLs
    - Remove email addresses
    - Remove excessive whitespace
    - Strip leading/trailing whitespace

    Does NOT remove stopwords or lemmatize (that's baseline-specific).
    """
    if not isinstance(text, str):
        return ""

    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r"http\S+|www\.\S+", "", text)

    # Remove email addresses
    text = re.sub(r"\S+@\S+", "", text)

    # Remove special characters but keep basic punctuation
    text = re.sub(r"[^\w\s.,!?;:'\"-]", "", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def preprocess_for_baseline(text: str) -> str:
    """
    Additional preprocessing for TF-IDF baseline:
    - Clean text (standard)
    - Remove stopwords
    - Lemmatize

    This produces a "bag of words" friendly representation.
    """
    text = clean_text(text)

    try:
        tokens = word_tokenize(text)
    except Exception:
        tokens = text.split()

    # Remove stopwords and lemmatize
    tokens = [
        LEMMATIZER.lemmatize(token)
        for token in tokens
        if token.isalpha() and token not in STOP_WORDS and len(token) > 2
    ]

    return " ".join(tokens)


def preprocess_for_transformer(text: str, max_length: int = 512) -> str:
    """
    Minimal preprocessing for DistilBERT:
    - Basic cleaning only (preserve casing for transformer)
    - No stopword removal (transformers learn this)
    - No lemmatization (subword tokenizer handles morphology)
    - Truncation handled by tokenizer, but we do a rough char-level truncation
      to avoid tokenizer memory issues on very long texts
    """
    if not isinstance(text, str):
        return ""

    # Remove URLs and emails only
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    # Rough truncation (~4 chars per token as heuristic)
    max_chars = max_length * 4
    if len(text) > max_chars:
        text = text[:max_chars]

    return text


def preprocess_dataset(
    df: pd.DataFrame,
    text_col: str = "full_text",
    method: str = "baseline",
) -> pd.DataFrame:
    """
    Apply preprocessing to entire dataset.

    Args:
        df: DataFrame with text column
        text_col: Name of the text column
        method: "baseline" (clean + stopwords + lemma) or "transformer" (minimal)

    Returns:
        DataFrame with new 'processed_text' column
    """
    df = df.copy()

    if method == "baseline":
        logger.info(f"Preprocessing {len(df)} texts for baseline (TF-IDF)...")
        df["processed_text"] = df[text_col].apply(preprocess_for_baseline)
    elif method == "transformer":
        logger.info(f"Preprocessing {len(df)} texts for transformer (DistilBERT)...")
        df["processed_text"] = df[text_col].apply(preprocess_for_transformer)
    else:
        raise ValueError(f"Unknown preprocessing method: {method}")

    # Remove empty rows after preprocessing
    empty_mask = df["processed_text"].str.strip() == ""
    if empty_mask.any():
        logger.warning(f"Removing {empty_mask.sum()} empty rows after preprocessing")
        df = df[~empty_mask]

    logger.info(f"Preprocessing complete. {len(df)} texts remaining.")
    return df
