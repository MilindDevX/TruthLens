"""
Baseline text model: TF-IDF + Logistic Regression.

Training pipeline:
1. Load and preprocess ISOT dataset
2. TF-IDF vectorization (max 10K features)
3. Logistic Regression with class_weight='balanced'
4. Hyperparameter tuning with Optuna (C, max_features)
5. Stratified 5-fold cross-validation
6. Full evaluation (metrics + fairness)
7. Save versioned model + metadata
"""

import os
import sys
import json
import joblib
import logging
import numpy as np
import optuna
from datetime import datetime, timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from ml.training.text.preprocess import preprocess_dataset
from ml.training.text.features import extract_features_batch, FEATURE_COLUMNS
from ml.training.utils.data_loader import load_isot_dataset, load_liar_dataset, split_dataset
from ml.training.utils.metrics import compute_all_metrics, log_metrics_summary, save_metrics
from ml.training.utils.logger import setup_training_logger

logger = setup_training_logger("truthlens.training.text_baseline", log_dir="logs")

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models", "text")


def create_objective(X_train, y_train, cv):
    """
    Create an Optuna objective function for hyperparameter tuning.
    Optimizes F1 score via cross-validation.
    """
    def objective(trial):
        # Hyperparameters to tune
        C = trial.suggest_float("C", 0.01, 100.0, log=True)
        max_features = trial.suggest_int("max_features", 3000, 15000, step=1000)
        ngram_max = trial.suggest_int("ngram_max", 1, 2)

        # Build pipeline
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                max_features=max_features,
                ngram_range=(1, ngram_max),
                sublinear_tf=True,
                min_df=2,
            )),
            ("clf", LogisticRegression(
                C=C,
                class_weight="balanced",
                max_iter=1000,
                solver="lbfgs",
                random_state=42,
            )),
        ])

        # Cross-validation with F1 scoring
        from sklearn.model_selection import cross_val_score
        scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="f1")
        return scores.mean()

    return objective


def train_baseline(
    n_optuna_trials: int = 30,
    version: str = "v1.0.0",
):
    """
    Full baseline training pipeline.

    Steps:
    1. Load ISOT dataset
    2. Preprocess for TF-IDF (stopwords + lemma)
    3. Extract features (for meta-model)
    4. Stratified 80/10/10 split
    5. Optuna hyperparameter tuning (F1-optimized)
    6. Train final model on full training set
    7. Evaluate on test set
    8. Validate on LIAR (OOD)
    9. Compute fairness metrics
    10. Save model + metadata
    """
    logger.info("=" * 60)
    logger.info("BASELINE MODEL: TF-IDF + Logistic Regression")
    logger.info("=" * 60)

    # Step 1: Load dataset
    logger.info("Step 1: Loading ISOT dataset...")
    df = load_isot_dataset()

    # Step 2: Preprocess
    logger.info("Step 2: Preprocessing for baseline...")
    df = preprocess_dataset(df, text_col="full_text", method="baseline")

    # Step 3: Extract features (saved for meta-model later)
    logger.info("Step 3: Extracting engineered features...")
    df = extract_features_batch(df, text_col="full_text")

    # Step 4: Split
    logger.info("Step 4: Splitting dataset (80/10/10, stratified)...")
    train_df, val_df, test_df = split_dataset(df, group_col="source")

    X_train = train_df["processed_text"].values
    y_train = train_df["label"].values
    X_val = val_df["processed_text"].values
    y_val = val_df["label"].values
    X_test = test_df["processed_text"].values
    y_test = test_df["label"].values

    # Step 5: Optuna tuning
    logger.info(f"Step 5: Hyperparameter tuning with Optuna ({n_optuna_trials} trials)...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    study = optuna.create_study(direction="maximize", study_name="tfidf_lr_baseline")
    study.optimize(
        create_objective(X_train, y_train, cv),
        n_trials=n_optuna_trials,
        show_progress_bar=True,
    )

    best_params = study.best_trial.params
    logger.info(f"Best params: {json.dumps(best_params, indent=2)}")
    logger.info(f"Best CV F1: {study.best_value:.4f}")

    # Step 6: Train final model with best params
    logger.info("Step 6: Training final model with best hyperparameters...")
    final_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=best_params["max_features"],
            ngram_range=(1, best_params["ngram_max"]),
            sublinear_tf=True,
            min_df=2,
        )),
        ("clf", LogisticRegression(
            C=best_params["C"],
            class_weight="balanced",
            max_iter=1000,
            solver="lbfgs",
            random_state=42,
        )),
    ])

    # Train on train + val for final model (test is held out)
    X_train_full = np.concatenate([X_train, X_val])
    y_train_full = np.concatenate([y_train, y_val])
    final_pipeline.fit(X_train_full, y_train_full)

    # Step 7: Evaluate on test set
    logger.info("Step 7: Evaluating on test set...")
    y_pred = final_pipeline.predict(X_test)
    y_prob = final_pipeline.predict_proba(X_test)[:, 1]

    test_metrics = compute_all_metrics(
        y_test, y_pred, y_prob,
        labels=["real", "fake"],
        group_labels=test_df["source"].values,
        group_name="source",
    )
    log_metrics_summary(test_metrics, "TF-IDF + Logistic Regression (Test)")

    # Step 8: OOD validation on LIAR
    logger.info("Step 8: Out-of-distribution validation on LIAR dataset...")
    try:
        liar_df = load_liar_dataset()
        liar_df = preprocess_dataset(liar_df, text_col="full_text", method="baseline")
        X_liar = liar_df["processed_text"].values
        y_liar = liar_df["label"].values

        y_liar_pred = final_pipeline.predict(X_liar)
        y_liar_prob = final_pipeline.predict_proba(X_liar)[:, 1]

        liar_metrics = compute_all_metrics(y_liar, y_liar_pred, y_liar_prob, labels=["real", "fake"])
        log_metrics_summary(liar_metrics, "TF-IDF + LR (LIAR OOD Validation)")

        test_metrics["ood_liar"] = {
            "accuracy": liar_metrics["accuracy"],
            "f1": liar_metrics["f1"],
            "recall": liar_metrics["recall"],
            "roc_auc": liar_metrics.get("roc_auc"),
        }
    except FileNotFoundError as e:
        logger.warning(f"LIAR dataset not available for OOD validation: {e}")
        test_metrics["ood_liar"] = None

    # Step 9: Save model + metadata
    logger.info(f"Step 9: Saving model version {version}...")
    model_dir = os.path.join(MODELS_DIR, version)
    os.makedirs(model_dir, exist_ok=True)

    # Save model
    model_path = os.path.join(model_dir, "model.pkl")
    joblib.dump(final_pipeline, model_path)

    # Save features for meta-model training
    train_features_df = train_df[FEATURE_COLUMNS + ["label"]].copy()
    train_features_df.to_csv(os.path.join(model_dir, "train_features.csv"), index=False)

    # Save metadata
    metadata = {
        "version": version,
        "model_type": "baseline",
        "architecture": "TF-IDF + Logistic Regression",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "ISOT Fake News",
        "dataset_size": len(df),
        "train_size": len(X_train_full),
        "test_size": len(X_test),
        "hyperparameters": best_params,
        "optuna_trials": n_optuna_trials,
        "best_cv_f1": round(study.best_value, 4),
        "metrics": {
            "accuracy": test_metrics["accuracy"],
            "precision": test_metrics["precision"],
            "recall": test_metrics["recall"],
            "f1": test_metrics["f1"],
            "roc_auc": test_metrics.get("roc_auc"),
        },
        "ood_validation": test_metrics.get("ood_liar"),
    }

    metadata_path = os.path.join(model_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    # Save full metrics
    save_metrics(test_metrics, os.path.join(model_dir, "evaluation_metrics.json"))

    logger.info(f"Model saved to {model_dir}")
    logger.info(f"Metadata saved to {metadata_path}")
    logger.info("=" * 60)
    logger.info("BASELINE TRAINING COMPLETE")
    logger.info("=" * 60)

    return final_pipeline, test_metrics


if __name__ == "__main__":
    train_baseline()
