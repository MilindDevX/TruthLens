"""
Production text inference service.

Holds loaded baseline (TF-IDF+LR via joblib) and advanced (DistilBERT via torch)
models in memory. Provides predict() and explain() with per-stage latency tracking!

Design:
- Thread-safe model references via asyncio.Lock (for reload safety)
- Graceful degradation: if advanced model missing → baseline-only mode
- CPU-optimized: torch.no_grad(), model.eval(), no CUDA pinning
- Reuses same preprocessing pipeline as training (no duplication)
"""

import sys
import os
import time
import asyncio
import logging
import numpy as np
import joblib
from typing import Optional
from dataclasses import dataclass, field

# Add project ml/ to path so we can import training preprocessing
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
_ml_root = os.path.join(_project_root, "ml")
if _ml_root not in sys.path:
    sys.path.insert(0, _project_root)

logger = logging.getLogger("truthlens.inference")


@dataclass
class InferenceTimings:
    """Per-request latency breakdown."""
    preprocess_ms: float = 0.0
    baseline_ms: float = 0.0
    advanced_ms: float = 0.0
    explain_ms: float = 0.0
    total_ms: float = 0.0


class TextInferenceService:
    """
    Production-grade text inference service.

    Manages loaded models and provides synchronous predict/explain
    wrapped in async for FastAPI compatibility.

    Attributes:
        baseline_pipeline: sklearn Pipeline (TF-IDF + LR) loaded via joblib
        advanced_model: DistilBERT model (torch)
        advanced_tokenizer: DistilBERT tokenizer
        version: active model version string
        _lock: asyncio.Lock for reload safety
    """

    def __init__(
        self,
        baseline_pipeline=None,
        advanced_model=None,
        advanced_tokenizer=None,
        version: str = "unknown",
        metadata: dict = None,
    ):
        self.baseline_pipeline = baseline_pipeline
        self.advanced_model = advanced_model
        self.advanced_tokenizer = advanced_tokenizer
        self.version = version
        self.metadata = metadata or {}
        self._lock = asyncio.Lock()

        # Track capabilities
        self.has_baseline = baseline_pipeline is not None
        self.has_advanced = advanced_model is not None and advanced_tokenizer is not None

        # Put advanced model in eval mode + no grad on init
        if self.has_advanced:
            self.advanced_model.eval()

        mode = []
        if self.has_baseline:
            mode.append("baseline")
        if self.has_advanced:
            mode.append("advanced")
        logger.info(f"TextInferenceService initialized: version={version}, models={mode}")

    async def predict(self, text: str) -> dict:
        """
        Run both models on preprocessed text and return structured result.

        Returns:
            {
                "baseline": {"prediction": "real"|"fake", "confidence": float, "probability": float},
                "advanced": {"prediction": "real"|"fake", "confidence": float, "probability": float},
                "timings": InferenceTimings,
                "explainability": ExplainabilityData | None,
            }

        Graceful degradation:
        - If advanced model is missing → baseline-only, advanced echoes baseline
        - If baseline is missing → error (at least one model required)
        """
        async with self._lock:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._predict_sync, text
            )

    def _predict_sync(self, text: str) -> dict:
        """Synchronous prediction logic (runs in thread pool)."""
        timings = InferenceTimings()
        total_start = time.perf_counter()

        # ── Step 1: Preprocess ──
        t0 = time.perf_counter()
        baseline_text = self._preprocess_baseline(text)
        advanced_text = self._preprocess_advanced(text)
        timings.preprocess_ms = round((time.perf_counter() - t0) * 1000, 2)

        result = {}

        # ── Step 2: Baseline inference ──
        if self.has_baseline:
            t0 = time.perf_counter()
            baseline_pred = self.baseline_pipeline.predict([baseline_text])[0]
            baseline_prob = self.baseline_pipeline.predict_proba([baseline_text])[0]
            timings.baseline_ms = round((time.perf_counter() - t0) * 1000, 2)

            result["baseline"] = {
                "prediction": "fake" if baseline_pred == 1 else "real",
                "confidence": round(float(max(baseline_prob)), 4),
                "probability": round(float(baseline_prob[1]), 4),  # P(fake)
            }
        else:
            result["baseline"] = {
                "prediction": "unknown",
                "confidence": 0.0,
                "probability": 0.5,
            }

        # ── Step 3: Advanced inference ──
        if self.has_advanced:
            t0 = time.perf_counter()
            result["advanced"] = self._predict_advanced(advanced_text)
            timings.advanced_ms = round((time.perf_counter() - t0) * 1000, 2)
        else:
            # Graceful degradation: echo baseline
            result["advanced"] = result["baseline"].copy()
            logger.debug("Advanced model not loaded — falling back to baseline")

        timings.total_ms = round((time.perf_counter() - total_start) * 1000, 2)
        result["timings"] = timings

        return result

    def _predict_advanced(self, text: str) -> dict:
        """Run DistilBERT inference on CPU."""
        import torch

        inputs = self.advanced_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )

        with torch.no_grad():
            outputs = self.advanced_model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]

        pred_class = torch.argmax(probs).item()
        confidence = float(probs[pred_class])
        prob_fake = float(probs[1])

        return {
            "prediction": "fake" if pred_class == 1 else "real",
            "confidence": round(confidence, 4),
            "probability": round(prob_fake, 4),
        }

    async def explain(self, text: str, top_k: int = 10) -> dict:
        """
        Generate explainability data for a prediction.

        Strategy:
        - If advanced model loaded → attention weights (fast, free)
        - If baseline only → SHAP LinearExplainer (fast for linear models)
        - Returns empty on failure (never blocks prediction)
        """
        async with self._lock:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._explain_sync, text, top_k
            )

    def _explain_sync(self, text: str, top_k: int = 10) -> dict:
        """Synchronous explainability logic."""
        t0 = time.perf_counter()

        try:
            if self.has_advanced:
                result = self._explain_attention(text, top_k)
            elif self.has_baseline:
                result = self._explain_shap(text, top_k)
            else:
                result = {"type": "none", "influential_tokens": []}

            explain_ms = round((time.perf_counter() - t0) * 1000, 2)
            result["explain_ms"] = explain_ms
            return result

        except Exception as e:
            logger.error(f"Explainability failed: {e}", exc_info=True)
            return {
                "type": "error",
                "influential_tokens": [],
                "error": str(e),
                "explain_ms": round((time.perf_counter() - t0) * 1000, 2),
            }

    def _explain_shap(self, text: str, top_k: int) -> dict:
        """SHAP LinearExplainer for baseline TF-IDF+LR."""
        import shap

        vectorizer = self.baseline_pipeline.named_steps["tfidf"]
        classifier = self.baseline_pipeline.named_steps["clf"]

        preprocessed = self._preprocess_baseline(text)
        X = vectorizer.transform([preprocessed])

        explainer = shap.LinearExplainer(
            classifier, X, feature_perturbation="interventional"
        )
        shap_values = explainer.shap_values(X)

        feature_names = vectorizer.get_feature_names_out()

        if isinstance(shap_values, list):
            values = shap_values[1][0]  # Positive class (fake)
        else:
            values = shap_values[0]

        top_indices = np.argsort(np.abs(values))[-top_k:][::-1]
        influential_tokens = [
            {"token": str(feature_names[i]), "impact": round(float(values[i]), 4)}
            for i in top_indices
            if abs(values[i]) > 1e-6
        ]

        return {"type": "shap", "influential_tokens": influential_tokens}

    def _explain_attention(self, text: str, top_k: int) -> dict:
        """Attention weight extraction from DistilBERT."""
        import torch

        inputs = self.advanced_tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        )

        with torch.no_grad():
            outputs = self.advanced_model(**inputs, output_attentions=True)

        # Last layer attention, averaged over heads, CLS row
        last_attn = outputs.attentions[-1]  # (1, heads, seq, seq)
        avg_attn = last_attn.mean(dim=1)[0]  # (seq, seq)
        cls_attn = avg_attn[0].numpy()  # CLS attention scores

        tokens = self.advanced_tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

        special = {"[CLS]", "[SEP]", "[PAD]"}
        token_scores = [
            (tok, float(score))
            for tok, score in zip(tokens, cls_attn)
            if tok not in special
        ]
        token_scores.sort(key=lambda x: x[1], reverse=True)

        influential_tokens = [
            {"token": t, "impact": round(s, 4)}
            for t, s in token_scores[:top_k]
        ]

        return {"type": "attention", "influential_tokens": influential_tokens}

    # ── Preprocessing (reuses training code) ──

    def _preprocess_baseline(self, text: str) -> str:
        """Preprocess for TF-IDF baseline (stopwords + lemma)."""
        try:
            from ml.training.text.preprocess import preprocess_for_baseline
            return preprocess_for_baseline(text)
        except ImportError:
            # Fallback: basic cleaning
            import re
            text = text.lower()
            text = re.sub(r"http\S+|www\.\S+", "", text)
            text = re.sub(r"\s+", " ", text)
            return text.strip()

    def _preprocess_advanced(self, text: str) -> str:
        """Preprocess for DistilBERT (minimal)."""
        try:
            from ml.training.text.preprocess import preprocess_for_transformer
            return preprocess_for_transformer(text)
        except ImportError:
            import re
            text = re.sub(r"http\S+|www\.\S+", "", text)
            text = re.sub(r"\s+", " ", text)
            return text.strip()

    # ── Feature extraction for meta-model ──

    def extract_features(self, text: str) -> dict:
        """Extract hand-crafted features for credibility meta-model."""
        try:
            from ml.training.text.features import extract_features
            return extract_features(text)
        except ImportError:
            return {
                "sentiment_extremity": 0.0,
                "content_length": len(text.split()),
                "keyword_manipulation_density": 0.0,
                "exclamation_ratio": 0.0,
                "caps_ratio": 0.0,
            }
