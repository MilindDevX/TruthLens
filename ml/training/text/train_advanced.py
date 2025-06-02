"""
Advanced text model: DistilBERT fine-tuned for fake news detection.

Training pipeline:
1. Load and minimally preprocess ISOT dataset
2. Tokenize with DistilBERT tokenizer (max 512 tokens)
3. Fine-tune DistilBERT + linear classification head
4. Hyperparameter tuning with Optuna (lr, batch_size, epochs)
5. Evaluation on test set + LIAR OOD validation
6. Save versioned model + metadata
"""

import os
import sys
import json
import logging
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from datetime import datetime, timezone
from sklearn.metrics import f1_score as sklearn_f1
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from ml.training.text.preprocess import preprocess_dataset
from ml.training.text.features import extract_features_batch, FEATURE_COLUMNS
from ml.training.utils.data_loader import load_isot_dataset, load_liar_dataset, split_dataset
from ml.training.utils.metrics import compute_all_metrics, log_metrics_summary, save_metrics
from ml.training.utils.logger import setup_training_logger, log_epoch_metrics

logger = setup_training_logger("truthlens.training.text_advanced", log_dir="logs")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models", "text")

# Device selection
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class TextDataset(Dataset):
    """PyTorch dataset for tokenized text."""

    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


class FocalLoss(nn.Module):
    """
    Focal loss for handling class imbalance.
    Focuses learning on hard-to-classify examples.
    """

    def __init__(self, alpha=None, gamma=2.0):
        super().__init__()
        self.alpha = alpha  # Class weights
        self.gamma = gamma

    def forward(self, logits, targets):
        ce_loss = nn.functional.cross_entropy(logits, targets, weight=self.alpha, reduction="none")
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss
        return focal_loss.mean()


def train_advanced(
    n_optuna_trials: int = 10,
    version: str = "v1.0.0",
    max_epochs: int = 5,
    patience: int = 2,
):
    """
    Full advanced model training pipeline.

    Uses DistilBERT with a linear classification head.
    Optimizes with Optuna on validation F1.
    Implements early stopping.
    """
    from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

    logger.info("=" * 60)
    logger.info("ADVANCED MODEL: DistilBERT Fine-tuned")
    logger.info(f"Device: {DEVICE}")
    logger.info("=" * 60)

    # Step 1: Load & preprocess
    logger.info("Step 1: Loading ISOT dataset...")
    df = load_isot_dataset()
    df = preprocess_dataset(df, text_col="full_text", method="transformer")
    df = extract_features_batch(df, text_col="full_text")

    # Step 2: Split
    logger.info("Step 2: Splitting dataset...")
    train_df, val_df, test_df = split_dataset(df, group_col="source")

    # Step 3: Tokenize
    logger.info("Step 3: Tokenizing with DistilBERT tokenizer...")
    tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

    def tokenize(texts, max_length=512):
        return tokenizer(
            texts.tolist(),
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )

    train_encodings = tokenize(train_df["processed_text"])
    val_encodings = tokenize(val_df["processed_text"])
    test_encodings = tokenize(test_df["processed_text"])

    train_dataset = TextDataset(train_encodings, train_df["label"].values)
    val_dataset = TextDataset(val_encodings, val_df["label"].values)
    test_dataset = TextDataset(test_encodings, test_df["label"].values)

    # Step 4: Compute class weights for focal loss
    class_counts = np.bincount(train_df["label"].values)
    total = class_counts.sum()
    class_weights = torch.tensor(
        [total / (2 * c) for c in class_counts],
        dtype=torch.float32,
    ).to(DEVICE)
    logger.info(f"Class weights: {class_weights.tolist()}")

    # Step 5: Optuna tuning
    logger.info(f"Step 5: Hyperparameter tuning ({n_optuna_trials} trials)...")

    import optuna

    def objective(trial):
        lr = trial.suggest_float("lr", 1e-5, 5e-5, log=True)
        batch_size = trial.suggest_categorical("batch_size", [16, 32])
        warmup_ratio = trial.suggest_float("warmup_ratio", 0.0, 0.1)
        weight_decay = trial.suggest_float("weight_decay", 0.0, 0.1)

        model = DistilBertForSequenceClassification.from_pretrained(
            "distilbert-base-uncased", num_labels=2
        ).to(DEVICE)

        optimizer = AdamW(
            model.parameters(), lr=lr, weight_decay=weight_decay
        )
        criterion = FocalLoss(alpha=class_weights, gamma=2.0)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=64)

        # Train for 2 epochs (quick evaluation for Optuna)
        model.train()
        for epoch in range(2):
            for batch in train_loader:
                optimizer.zero_grad()
                input_ids = batch["input_ids"].to(DEVICE)
                attention_mask = batch["attention_mask"].to(DEVICE)
                labels = batch["labels"].to(DEVICE)

                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                loss = criterion(outputs.logits, labels)
                loss.backward()
                optimizer.step()

        # Evaluate on validation set
        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(DEVICE)
                attention_mask = batch["attention_mask"].to(DEVICE)
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=-1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(batch["labels"].numpy())

        f1 = sklearn_f1(all_labels, all_preds)
        return f1

    study = optuna.create_study(direction="maximize", study_name="distilbert_advanced")
    study.optimize(objective, n_trials=n_optuna_trials, show_progress_bar=True)
    best_params = study.best_trial.params
    logger.info(f"Best params: {json.dumps(best_params, indent=2)}")

    # Step 6: Train final model with best params + early stopping
    logger.info("Step 6: Training final model with early stopping...")
    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=2
    ).to(DEVICE)

    optimizer = AdamW(
        model.parameters(),
        lr=best_params["lr"],
        weight_decay=best_params["weight_decay"],
    )
    criterion = FocalLoss(alpha=class_weights, gamma=2.0)

    train_loader = DataLoader(
        train_dataset, batch_size=best_params["batch_size"], shuffle=True
    )
    val_loader = DataLoader(val_dataset, batch_size=64)

    best_val_f1 = 0
    patience_counter = 0

    for epoch in range(max_epochs):
        # Training
        model.train()
        total_loss = 0
        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["labels"].to(DEVICE)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss = criterion(outputs.logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)

        # Validation
        model.eval()
        all_preds, all_labels = [], []
        val_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(DEVICE)
                attention_mask = batch["attention_mask"].to(DEVICE)
                labels_batch = batch["labels"].to(DEVICE)

                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                loss = criterion(outputs.logits, labels_batch)
                val_loss += loss.item()

                preds = torch.argmax(outputs.logits, dim=-1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(batch["labels"].numpy())

        avg_val_loss = val_loss / len(val_loader)
        val_f1 = sklearn_f1(all_labels, all_preds)

        log_epoch_metrics(
            logger, epoch + 1, avg_train_loss, avg_val_loss,
            {"val_f1": round(val_f1, 4)},
        )

        # Early stopping
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            patience_counter = 0
            # Save best checkpoint
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch + 1}")
                break

    # Load best checkpoint
    model.load_state_dict(best_state)
    model.to(DEVICE)

    # Step 7: Evaluate on test set
    logger.info("Step 7: Evaluating on test set...")
    model.eval()
    test_loader = DataLoader(test_dataset, batch_size=64)
    all_preds, all_labels, all_probs = [], [], []

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=-1)
            preds = torch.argmax(probs, dim=-1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(batch["labels"].numpy())
            all_probs.extend(probs[:, 1].cpu().numpy())

    test_metrics = compute_all_metrics(
        np.array(all_labels), np.array(all_preds), np.array(all_probs),
        labels=["real", "fake"],
        group_labels=test_df["source"].values,
        group_name="source",
    )
    log_metrics_summary(test_metrics, "DistilBERT (Test)")

    # Step 8: OOD validation on LIAR
    logger.info("Step 8: OOD validation on LIAR...")
    try:
        liar_df = load_liar_dataset()
        liar_df = preprocess_dataset(liar_df, text_col="full_text", method="transformer")
        liar_encodings = tokenize(liar_df["processed_text"])
        liar_dataset = TextDataset(liar_encodings, liar_df["label"].values)
        liar_loader = DataLoader(liar_dataset, batch_size=64)

        liar_preds, liar_labels, liar_probs = [], [], []
        with torch.no_grad():
            for batch in liar_loader:
                input_ids = batch["input_ids"].to(DEVICE)
                attention_mask = batch["attention_mask"].to(DEVICE)
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                probs = torch.softmax(outputs.logits, dim=-1)
                preds = torch.argmax(probs, dim=-1)
                liar_preds.extend(preds.cpu().numpy())
                liar_labels.extend(batch["labels"].numpy())
                liar_probs.extend(probs[:, 1].cpu().numpy())

        liar_metrics = compute_all_metrics(
            np.array(liar_labels), np.array(liar_preds), np.array(liar_probs),
        )
        log_metrics_summary(liar_metrics, "DistilBERT (LIAR OOD)")
        test_metrics["ood_liar"] = {
            "accuracy": liar_metrics["accuracy"],
            "f1": liar_metrics["f1"],
            "recall": liar_metrics["recall"],
        }
    except FileNotFoundError as e:
        logger.warning(f"LIAR not available: {e}")
        test_metrics["ood_liar"] = None

    # Step 9: Save model + metadata
    logger.info(f"Step 9: Saving model version {version}...")
    model_dir = os.path.join(MODELS_DIR, f"{version}_advanced")
    os.makedirs(model_dir, exist_ok=True)

    # Save model weights
    model.cpu()
    torch.save(model.state_dict(), os.path.join(model_dir, "model.pt"))
    tokenizer.save_pretrained(os.path.join(model_dir, "tokenizer"))

    # Save features for meta-model
    train_features = train_df[FEATURE_COLUMNS + ["label"]].copy()
    train_features.to_csv(os.path.join(model_dir, "train_features.csv"), index=False)

    # Save metadata
    metadata = {
        "version": version,
        "model_type": "advanced",
        "architecture": "DistilBERT (fine-tuned)",
        "base_model": "distilbert-base-uncased",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "ISOT Fake News",
        "device": str(DEVICE),
        "hyperparameters": best_params,
        "epochs_trained": epoch + 1 if patience_counter >= patience else max_epochs,
        "metrics": {
            "accuracy": test_metrics["accuracy"],
            "precision": test_metrics["precision"],
            "recall": test_metrics["recall"],
            "f1": test_metrics["f1"],
            "roc_auc": test_metrics.get("roc_auc"),
        },
        "ood_validation": test_metrics.get("ood_liar"),
    }

    with open(os.path.join(model_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    save_metrics(test_metrics, os.path.join(model_dir, "evaluation_metrics.json"))

    logger.info("=" * 60)
    logger.info("ADVANCED TRAINING COMPLETE")
    logger.info("=" * 60)

    return model, tokenizer, test_metrics


if __name__ == "__main__":
    train_advanced()
