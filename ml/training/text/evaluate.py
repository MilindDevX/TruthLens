"""
Model evaluation and comparison module.

Loads both baseline and advanced models, runs them on the same test set,
and produces a side-by-side comparison report with all required metrics.
"""

import os
import sys
import json
import logging
import numpy as np
import joblib
import torch
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from ml.training.text.preprocess import preprocess_dataset
from ml.training.utils.data_loader import load_isot_dataset, split_dataset
from ml.training.utils.metrics import compute_all_metrics, log_metrics_summary, save_metrics
from ml.training.utils.logger import setup_training_logger

logger = setup_training_logger("truthlens.training.evaluate")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models", "text")


def evaluate_and_compare(version: str = "v1.0.0"):
    """
    Compare baseline vs advanced model on the same test set.

    Produces:
    - Side-by-side metrics table
    - Recommendation for production use
    - Saved comparison report
    """
    logger.info("=" * 60)
    logger.info("MODEL COMPARISON: Baseline vs Advanced")
    logger.info("=" * 60)

    # Load and preprocess data
    df = load_isot_dataset()
    _, _, test_df = split_dataset(df, group_col="source")

    results = {}

    # --- Evaluate Baseline ---
    logger.info("\n--- Evaluating Baseline (TF-IDF + LR) ---")
    baseline_path = os.path.join(MODELS_DIR, version, "model.pkl")
    if os.path.exists(baseline_path):
        baseline = joblib.load(baseline_path)
        test_baseline = preprocess_dataset(test_df.copy(), text_col="full_text", method="baseline")

        y_pred = baseline.predict(test_baseline["processed_text"].values)
        y_prob = baseline.predict_proba(test_baseline["processed_text"].values)[:, 1]

        baseline_metrics = compute_all_metrics(
            test_df["label"].values, y_pred, y_prob,
            labels=["real", "fake"],
            group_labels=test_df["source"].values,
        )
        log_metrics_summary(baseline_metrics, "Baseline (TF-IDF + LR)")
        results["baseline"] = baseline_metrics
    else:
        logger.warning(f"Baseline model not found at {baseline_path}")

    # --- Evaluate Advanced ---
    logger.info("\n--- Evaluating Advanced (DistilBERT) ---")
    advanced_path = os.path.join(MODELS_DIR, f"{version}_advanced", "model.pt")
    if os.path.exists(advanced_path):
        from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
        from ml.training.text.train_advanced import TextDataset

        tokenizer = DistilBertTokenizer.from_pretrained(
            os.path.join(MODELS_DIR, f"{version}_advanced", "tokenizer")
        )
        model = DistilBertForSequenceClassification.from_pretrained(
            "distilbert-base-uncased", num_labels=2
        )
        model.load_state_dict(torch.load(advanced_path, map_location="cpu"))
        model.eval()

        test_advanced = preprocess_dataset(test_df.copy(), text_col="full_text", method="transformer")
        encodings = tokenizer(
            test_advanced["processed_text"].tolist(),
            padding=True, truncation=True, max_length=512, return_tensors="pt",
        )

        from torch.utils.data import DataLoader
        dataset = TextDataset(encodings, test_df["label"].values)
        loader = DataLoader(dataset, batch_size=64)

        all_preds, all_probs = [], []
        with torch.no_grad():
            for batch in loader:
                outputs = model(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                )
                probs = torch.softmax(outputs.logits, dim=-1)
                all_preds.extend(torch.argmax(probs, dim=-1).numpy())
                all_probs.extend(probs[:, 1].numpy())

        advanced_metrics = compute_all_metrics(
            test_df["label"].values, np.array(all_preds), np.array(all_probs),
            labels=["real", "fake"],
            group_labels=test_df["source"].values,
        )
        log_metrics_summary(advanced_metrics, "Advanced (DistilBERT)")
        results["advanced"] = advanced_metrics
    else:
        logger.warning(f"Advanced model not found at {advanced_path}")

    # --- Comparison ---
    if "baseline" in results and "advanced" in results:
        logger.info("\n" + "=" * 60)
        logger.info("COMPARISON TABLE")
        logger.info("=" * 60)

        comparison = {}
        for metric in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
            b = results["baseline"].get(metric, "N/A")
            a = results["advanced"].get(metric, "N/A")
            winner = "advanced" if (isinstance(a, float) and isinstance(b, float) and a > b) else "baseline"
            comparison[metric] = {"baseline": b, "advanced": a, "winner": winner}
            logger.info(f"  {metric:>12}: Baseline={b}  Advanced={a}  Winner={winner}")

        # Recommendation
        adv_f1 = results["advanced"].get("f1", 0)
        base_f1 = results["baseline"].get("f1", 0)
        adv_recall = results["advanced"].get("recall", 0)
        base_recall = results["baseline"].get("recall", 0)

        if adv_recall >= 0.85 and adv_f1 > base_f1:
            recommendation = "advanced"
            reason = f"Advanced model meets recall target (≥0.85) with {adv_recall} and has higher F1 ({adv_f1} vs {base_f1})"
        elif base_recall >= 0.85 and base_f1 >= adv_f1:
            recommendation = "baseline"
            reason = f"Baseline meets recall target with {base_recall} and matches/exceeds F1. Faster inference."
        else:
            recommendation = "advanced"
            reason = f"Advanced has better recall ({adv_recall} vs {base_recall}), though target may not be met."

        logger.info(f"\nRECOMMENDATION: {recommendation}")
        logger.info(f"REASON: {reason}")

        # Save comparison report
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "comparison": comparison,
            "recommendation": recommendation,
            "reason": reason,
            "recall_target": 0.85,
        }
        report_path = os.path.join(MODELS_DIR, "comparison_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Comparison report saved to {report_path}")

    return results


if __name__ == "__main__":
    evaluate_and_compare()
