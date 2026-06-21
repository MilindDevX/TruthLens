"""
Lightweight drift detection for production inference.

Monitors:
- Rolling window of recent prediction confidences
- KL divergence between training confidence distribution and recent predictions
- Rolling average prediction class balance

Alerts via structured JSON logging when drift thresholds are exceeded.
Does NOT block or slow down inference — purely observational.
"""

import logging
import numpy as np
from collections import deque
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger("truthlens.drift")

# Default training confidence distribution (will be overridden from metadata)
# 10 bins: [0.0-0.1, 0.1-0.2, ..., 0.9-1.0]
DEFAULT_TRAINING_DIST = np.array([
    0.01, 0.02, 0.03, 0.04, 0.05,  # Low confidence bins (rare in training)
    0.05, 0.10, 0.15, 0.25, 0.30,  # High confidence bins (common in training)
])
DEFAULT_TRAINING_DIST = DEFAULT_TRAINING_DIST / DEFAULT_TRAINING_DIST.sum()


@dataclass
class DriftStats:
    """Current drift statistics."""
    kl_divergence: Optional[float] = None
    mean_confidence: Optional[float] = None
    recent_positive_rate: Optional[float] = None
    window_size: int = 0
    max_window: int = 0
    alert: bool = False
    alert_reason: Optional[str] = None


class DriftMonitor:
    """
    Rolling-window drift monitor for production inference.

    Tracks the last N prediction confidences and computes:
    1. KL divergence from training distribution
    2. Mean confidence (sudden drops signal distribution shift)
    3. Positive prediction rate (class balance drift)

    Thread-safe: uses deque (thread-safe for append/popleft).
    """

    def __init__(
        self,
        window_size: int = 1000,
        training_distribution: Optional[np.ndarray] = None,
        kl_threshold: float = 0.5,
        confidence_alert_low: float = 0.55,
        class_balance_threshold: float = 0.3,
    ):
        """
        Args:
            window_size: Number of recent predictions to track
            training_distribution: 10-bin histogram of training confidences (normalized)
            kl_threshold: KL divergence above this triggers alert
            confidence_alert_low: Mean confidence below this triggers alert
            class_balance_threshold: Alert if positive rate deviates more than this from 0.5
        """
        self.window_size = window_size
        self.training_dist = training_distribution if training_distribution is not None else DEFAULT_TRAINING_DIST
        self.kl_threshold = kl_threshold
        self.confidence_alert_low = confidence_alert_low
        self.class_balance_threshold = class_balance_threshold

        # Rolling windows (deque is thread-safe for append/popleft)
        self._confidences: deque[float] = deque(maxlen=window_size)
        self._predictions: deque[int] = deque(maxlen=window_size)  # 0=real, 1=fake

    def record(self, confidence: float, prediction: int) -> None:
        """
        Record a single prediction result.
        Called after every inference — must be fast.
        """
        self._confidences.append(confidence)
        self._predictions.append(prediction)

    def get_stats(self) -> DriftStats:
        """
        Compute current drift statistics from rolling window.
        Non-blocking, can be called from health endpoint.
        """
        n = len(self._confidences)
        if n < 50:
            return DriftStats(window_size=n, max_window=self.window_size)

        confidences = np.array(self._confidences)
        predictions = np.array(self._predictions)

        # Mean confidence
        mean_conf = float(np.mean(confidences))

        # Positive prediction rate
        pos_rate = float(np.mean(predictions))

        # KL divergence: bin recent confidences into 10 bins
        recent_hist, _ = np.histogram(confidences, bins=10, range=(0.0, 1.0))
        recent_dist = recent_hist.astype(float)
        recent_dist = (recent_dist + 1e-10) / (recent_dist.sum() + 1e-10 * 10)  # Smoothing

        training_dist = self.training_dist.copy()
        training_dist = (training_dist + 1e-10) / (training_dist.sum() + 1e-10 * 10)

        kl_div = float(np.sum(recent_dist * np.log(recent_dist / training_dist)))

        # Check alerts
        alert = False
        alert_reason = None

        if kl_div > self.kl_threshold:
            alert = True
            alert_reason = f"KL divergence {kl_div:.4f} exceeds threshold {self.kl_threshold}"
            logger.warning(f"DRIFT ALERT: {alert_reason}")

        if mean_conf < self.confidence_alert_low:
            alert = True
            reason = f"Mean confidence {mean_conf:.4f} below threshold {self.confidence_alert_low}"
            alert_reason = f"{alert_reason}; {reason}" if alert_reason else reason
            logger.warning(f"DRIFT ALERT: {reason}")

        if abs(pos_rate - 0.5) > self.class_balance_threshold:
            alert = True
            reason = f"Class balance drift: positive_rate={pos_rate:.4f} (threshold ±{self.class_balance_threshold})"
            alert_reason = f"{alert_reason}; {reason}" if alert_reason else reason
            logger.warning(f"DRIFT ALERT: {reason}")

        return DriftStats(
            kl_divergence=round(kl_div, 4),
            mean_confidence=round(mean_conf, 4),
            recent_positive_rate=round(pos_rate, 4),
            window_size=n,
            max_window=self.window_size,
            alert=alert,
            alert_reason=alert_reason,
        )

    def to_dict(self) -> dict:
        """Serialize stats for JSON response (health endpoint)."""
        stats = self.get_stats()
        return {
            "kl_divergence": stats.kl_divergence,
            "mean_confidence": stats.mean_confidence,
            "recent_positive_rate": stats.recent_positive_rate,
            "window_size": stats.window_size,
            "max_window": stats.max_window,
            "alert": stats.alert,
            "alert_reason": stats.alert_reason,
        }

    def reset(self) -> None:
        """Clear rolling windows (e.g., after model reload)."""
        self._confidences.clear()
        self._predictions.clear()
        logger.info("Drift monitor reset")
