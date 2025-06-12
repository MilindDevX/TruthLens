"""
Shared metrics computation for model evaluation.

Computes all required metrics:
- Accuracy, Precision, Recall, F1
- ROC-AUC
- Confusion Matrix
- Classification Report
- Calibration Analysis
- Fairness Metrics (per-group false positive rates)
"""

import numpy as np
from typing import Optional
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    calibration_curve,
)
import json
import logging

logger = logging.getLogger("truthlens.ml.metrics")


def compute_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None,
    labels: list[str] = None,
    group_labels: Optional[np.ndarray] = None,
    group_name: str = "source",
) -> dict:
    """
    Compute the full metrics suite required by Phase 4.

    Args:
        y_true: Ground truth binary labels (0/1)
        y_pred: Predicted binary labels (0/1)
        y_prob: Predicted probabilities for positive class (for ROC-AUC, calibration)
        labels: Class label names (e.g., ["real", "fake"])
        group_labels: Optional group labels for fairness metrics (e.g., source name)
        group_name: Name of the grouping variable for fairness reporting

    Returns:
        Dict with all metrics including fairness analysis
    """
    if labels is None:
        labels = ["real", "fake"]

    metrics = {}

    # Core metrics
    metrics["accuracy"] = round(accuracy_score(y_true, y_pred), 4)
    metrics["precision"] = round(precision_score(y_true, y_pred, zero_division=0), 4)
    metrics["recall"] = round(recall_score(y_true, y_pred, zero_division=0), 4)
    metrics["f1"] = round(f1_score(y_true, y_pred, zero_division=0), 4)

    # ROC-AUC (requires probabilities)
    if y_prob is not None:
        try:
            metrics["roc_auc"] = round(roc_auc_score(y_true, y_prob), 4)
        except ValueError as e:
            logger.warning(f"ROC-AUC computation failed: {e}")
            metrics["roc_auc"] = None
    else:
        metrics["roc_auc"] = None

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    metrics["confusion_matrix"] = {
        "matrix": cm.tolist(),
        "labels": labels,
        "tn": int(cm[0, 0]),
        "fp": int(cm[0, 1]),
        "fn": int(cm[1, 0]),
        "tp": int(cm[1, 1]),
    }

    # Classification report
    metrics["classification_report"] = classification_report(
        y_true, y_pred, target_names=labels, output_dict=True, zero_division=0
    )

    # Calibration analysis (if probabilities available)
    if y_prob is not None:
        try:
            prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
            metrics["calibration"] = {
                "prob_true": prob_true.tolist(),
                "prob_pred": prob_pred.tolist(),
                "calibration_error": round(
                    float(np.mean(np.abs(prob_true - prob_pred))), 4
                ),
            }
        except Exception as e:
            logger.warning(f"Calibration analysis failed: {e}")
            metrics["calibration"] = None
    else:
        metrics["calibration"] = None

    # Fairness metrics (per-group false positive rates)
    if group_labels is not None:
        metrics["fairness"] = compute_fairness_metrics(
            y_true, y_pred, group_labels, group_name
        )
    else:
        metrics["fairness"] = None

    return metrics


def compute_fairness_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    group_labels: np.ndarray,
    group_name: str = "source",
) -> dict:
    """
    Compute per-group fairness metrics:
    - False positive rate per group
    - False negative rate per group
    - Equalized odds check
    - Demographic parity check

    Used to detect source-bias, political-leaning skew, etc.
    """
    unique_groups = np.unique(group_labels)
    group_metrics = {}

    for group in unique_groups:
        mask = group_labels == group
        group_true = y_true[mask]
        group_pred = y_pred[mask]

        if len(group_true) == 0:
            continue

        cm = confusion_matrix(group_true, group_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
        positive_rate = np.mean(group_pred)

        group_metrics[str(group)] = {
            "count": int(len(group_true)),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "true_positive_rate": round(tpr, 4),
            "positive_prediction_rate": round(positive_rate, 4),
        }

    # Equalized odds: max difference in TPR and FPR across groups
    tprs = [m["true_positive_rate"] for m in group_metrics.values()]
    fprs = [m["false_positive_rate"] for m in group_metrics.values()]

    return {
        "group_name": group_name,
        "per_group": group_metrics,
        "equalized_odds_gap": {
            "tpr_gap": round(max(tprs) - min(tprs), 4) if tprs else None,
            "fpr_gap": round(max(fprs) - min(fprs), 4) if fprs else None,
        },
        "demographic_parity_gap": round(
            max(m["positive_prediction_rate"] for m in group_metrics.values())
            - min(m["positive_prediction_rate"] for m in group_metrics.values()),
            4,
        ) if group_metrics else None,
    }


def log_metrics_summary(metrics: dict, model_name: str) -> None:
    """Log a human-readable summary of key metrics."""
    logger.info(
        f"\n{'='*60}\n"
        f"Model: {model_name}\n"
        f"{'='*60}\n"
        f"Accuracy:  {metrics['accuracy']}\n"
        f"Precision: {metrics['precision']}\n"
        f"Recall:    {metrics['recall']}\n"
        f"F1:        {metrics['f1']}\n"
        f"ROC-AUC:   {metrics.get('roc_auc', 'N/A')}\n"
        f"{'='*60}"
    )


def save_metrics(metrics: dict, filepath: str) -> None:
    """Save metrics to JSON file."""
    with open(filepath, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"Metrics saved to {filepath}")
