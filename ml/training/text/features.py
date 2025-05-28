"""
Feature engineering for meta-model stacking.

Extracts hand-crafted features from text:
- sentiment_extremity (VADER compound abs)
- content_length (word count)
- keyword_manipulation_density (sensational trigger words ratio)
- exclamation_ratio
- caps_ratio

These features feed the meta-model alongside model probabilities.
"""

import re
import logging
import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger("truthlens.ml.features")

# VADER sentiment analyzer
_analyzer = SentimentIntensityAnalyzer()

# Sensational / manipulative trigger words
TRIGGER_WORDS = {
    "breaking", "shocking", "explosive", "bombshell", "urgent",
    "exclusive", "scandal", "exposed", "revealed", "secret",
    "corrupt", "conspiracy", "hoax", "coverup", "leaked",
    "unbelievable", "incredible", "terrifying", "horrifying",
    "outrageous", "disgusting", "insane", "massive", "huge",
    "destroy", "attack", "slam", "blast", "rip", "savage",
    "allegedly", "sources say", "reportedly", "claim",
    "you won't believe", "they don't want you to know",
    "the truth about", "wake up", "mainstream media",
}


def extract_features(text: str) -> dict:
    """
    Extract hand-crafted features from a single text.

    Returns dict with:
    - sentiment_extremity: abs(VADER compound score). Higher = more extreme sentiment.
    - content_length: word count
    - keyword_manipulation_density: ratio of trigger words to total words
    - exclamation_ratio: ! count / total punctuation count
    - caps_ratio: proportion of UPPERCASE words
    """
    if not isinstance(text, str) or not text.strip():
        return {
            "sentiment_extremity": 0.0,
            "content_length": 0,
            "keyword_manipulation_density": 0.0,
            "exclamation_ratio": 0.0,
            "caps_ratio": 0.0,
        }

    words = text.split()
    word_count = len(words)

    # Sentiment extremity
    sentiment = _analyzer.polarity_scores(text)
    sentiment_extremity = abs(sentiment["compound"])

    # Keyword manipulation density
    text_lower = text.lower()
    trigger_count = sum(1 for word in TRIGGER_WORDS if word in text_lower)
    keyword_density = trigger_count / max(word_count, 1)

    # Exclamation ratio
    punctuation_count = len(re.findall(r"[.!?,;:]", text))
    exclamation_count = text.count("!")
    exclamation_ratio = exclamation_count / max(punctuation_count, 1)

    # Caps ratio (proportion of all-caps words, excluding short words)
    caps_words = sum(1 for w in words if w.isupper() and len(w) > 1)
    caps_ratio = caps_words / max(word_count, 1)

    return {
        "sentiment_extremity": round(sentiment_extremity, 4),
        "content_length": word_count,
        "keyword_manipulation_density": round(keyword_density, 4),
        "exclamation_ratio": round(exclamation_ratio, 4),
        "caps_ratio": round(caps_ratio, 4),
    }


def extract_features_batch(
    df: pd.DataFrame,
    text_col: str = "full_text",
) -> pd.DataFrame:
    """
    Extract features for an entire dataset.
    Adds feature columns to the DataFrame.

    Args:
        df: DataFrame with text column
        text_col: Name of the raw text column (not preprocessed)

    Returns:
        DataFrame with added feature columns
    """
    logger.info(f"Extracting features from {len(df)} texts...")

    features = df[text_col].apply(extract_features)
    features_df = pd.DataFrame(features.tolist())

    result = pd.concat([df.reset_index(drop=True), features_df], axis=1)

    logger.info("Feature extraction complete. Feature summary:")
    for col in features_df.columns:
        logger.info(f"  {col}: mean={features_df[col].mean():.4f}, std={features_df[col].std():.4f}")

    return result


FEATURE_COLUMNS = [
    "sentiment_extremity",
    "content_length",
    "keyword_manipulation_density",
    "exclamation_ratio",
    "caps_ratio",
]
