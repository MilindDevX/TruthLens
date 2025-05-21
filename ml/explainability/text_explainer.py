"""
Explainability module for TruthLens X.

Provides:
1. SHAP explanations for baseline (TF-IDF + LR)
2. Attention weight extraction for DistilBERT
3. LIME fallback for any model
"""

import logging
import numpy as np
from typing import Optional

logger = logging.getLogger("truthlens.ml.explainability")


def explain_baseline_shap(
    pipeline,
    text: str,
    top_k: int = 10,
) -> dict:
    """
    Generate SHAP explanations for a baseline (TF-IDF + LR) prediction.

    Uses SHAP LinearExplainer which is fast for linear models.

    Args:
        pipeline: sklearn Pipeline with TfidfVectorizer + LogisticRegression
        text: Input text to explain
        top_k: Number of top influential tokens to return

    Returns:
        dict with type="shap" and influential_tokens list
    """
    try:
        import shap

        # Extract components from the pipeline
        vectorizer = pipeline.named_steps["tfidf"]
        classifier = pipeline.named_steps["clf"]

        # Vectorize input
        X = vectorizer.transform([text])

        # Use LinearExplainer for speed
        explainer = shap.LinearExplainer(classifier, X, feature_perturbation="interventional")
        shap_values = explainer.shap_values(X)

        # Get feature names
        feature_names = vectorizer.get_feature_names_out()

        # For binary classification, shap_values may be 2D
        if isinstance(shap_values, list):
            values = shap_values[1][0]  # Positive class (fake)
        else:
            values = shap_values[0]

        # Get top-k tokens by absolute SHAP value
        top_indices = np.argsort(np.abs(values))[-top_k:][::-1]
        influential_tokens = [
            {"token": feature_names[i], "impact": round(float(values[i]), 4)}
            for i in top_indices
            if values[i] != 0  # Skip zero-impact tokens
        ]

        return {
            "type": "shap",
            "influential_tokens": influential_tokens,
        }

    except Exception as e:
        logger.error(f"SHAP explanation failed: {e}")
        return {"type": "shap", "influential_tokens": [], "error": str(e)}


def explain_distilbert_attention(
    model,
    tokenizer,
    text: str,
    top_k: int = 10,
) -> dict:
    """
    Extract attention weights from DistilBERT as explanation.

    Uses the attention scores from the last transformer layer,
    averaged across all heads. Higher attention = more influential token.

    Args:
        model: DistilBERT model with output_attentions=True
        tokenizer: DistilBERT tokenizer
        text: Input text
        top_k: Number of top tokens

    Returns:
        dict with type="attention" and influential_tokens
    """
    try:
        import torch

        model.eval()
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

        with torch.no_grad():
            outputs = model(**inputs, output_attentions=True)

        # Average attention across all heads and layers
        # attentions: tuple of (batch, num_heads, seq_len, seq_len)
        attentions = outputs.attentions
        last_layer_attention = attentions[-1]  # Last layer
        avg_attention = last_layer_attention.mean(dim=1)[0]  # Average over heads

        # CLS token attention scores (row 0—what CLS attends to)
        cls_attention = avg_attention[0].numpy()

        # Get tokens
        tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

        # Exclude [CLS], [SEP], [PAD]
        special_tokens = {"[CLS]", "[SEP]", "[PAD]"}
        token_scores = [
            (token, float(score))
            for token, score in zip(tokens, cls_attention)
            if token not in special_tokens
        ]

        # Sort by attention score
        token_scores.sort(key=lambda x: x[1], reverse=True)
        influential_tokens = [
            {"token": t, "impact": round(s, 4)}
            for t, s in token_scores[:top_k]
        ]

        return {
            "type": "attention",
            "influential_tokens": influential_tokens,
        }

    except Exception as e:
        logger.error(f"Attention explanation failed: {e}")
        return {"type": "attention", "influential_tokens": [], "error": str(e)}


def explain_lime(
    predict_fn,
    text: str,
    top_k: int = 10,
    num_samples: int = 500,
) -> dict:
    """
    LIME-based explanation for any model.

    Generates local perturbations of the input text and observes
    how the prediction changes. Slower but model-agnostic.

    Args:
        predict_fn: function that takes list[str] → np.array of probabilities
        text: Input text
        top_k: Number of top features
        num_samples: Number of perturbed samples (lower = faster, noisier)

    Returns:
        dict with type="lime" and influential_tokens
    """
    try:
        from lime.lime_text import LimeTextExplainer

        explainer = LimeTextExplainer(class_names=["real", "fake"])
        explanation = explainer.explain_instance(
            text,
            predict_fn,
            num_features=top_k,
            num_samples=num_samples,
        )

        influential_tokens = [
            {"token": word, "impact": round(weight, 4)}
            for word, weight in explanation.as_list()
        ]

        return {
            "type": "lime",
            "influential_tokens": influential_tokens,
        }

    except Exception as e:
        logger.error(f"LIME explanation failed: {e}")
        return {"type": "lime", "influential_tokens": [], "error": str(e)}
