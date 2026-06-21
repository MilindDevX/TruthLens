"""
Training logger utility.
Provides structured logging for ML training pipelines.
"""

import logging
import json
import os
from datetime import datetime, timezone


def setup_training_logger(
    name: str,
    log_dir: str = None,
    log_level: int = logging.INFO,
) -> logging.Logger:
    """
    Set up a logger for training pipelines with both console and file output.

    Args:
        name: Logger name (e.g., "truthlens.training.text_baseline")
        log_dir: Directory for log files (creates if needed)
        log_level: Logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Console handler (human-readable)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (JSON structured)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"{name.split('.')[-1]}_{timestamp}.log")

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_format = logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def log_experiment_config(logger: logging.Logger, config: dict) -> None:
    """Log experiment configuration as structured JSON."""
    logger.info(f"Experiment config: {json.dumps(config, indent=2, default=str)}")


def log_epoch_metrics(
    logger: logging.Logger,
    epoch: int,
    train_loss: float,
    val_loss: float = None,
    metrics: dict = None,
) -> None:
    """Log per-epoch training metrics."""
    entry = {
        "epoch": epoch,
        "train_loss": round(train_loss, 4),
    }
    if val_loss is not None:
        entry["val_loss"] = round(val_loss, 4)
    if metrics:
        entry.update(metrics)

    logger.info(f"Epoch metrics: {json.dumps(entry)}")
