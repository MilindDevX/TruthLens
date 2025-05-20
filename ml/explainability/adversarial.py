"""
Adversarial robustness testing for text models.

Tests model resilience against:
1. Character swaps (typosquatting: "the" → "teh")
2. Synonym replacement (WordNet-based)
3. Random character insertion/deletion
"""

import re
import random
import logging
import numpy as np
from typing import Callable, Optional
from copy import deepcopy

logger = logging.getLogger("truthlens.ml.adversarial")


def char_swap(text: str, swap_rate: float = 0.05) -> str:
    """
    Randomly swap adjacent characters at the given rate.
    Simulates typos (e.g., "breaking" → "brekiang").
    """
    chars = list(text)
    n_swaps = max(1, int(len(chars) * swap_rate))

    for _ in range(n_swaps):
        idx = random.randint(0, len(chars) - 2)
        if chars[idx].isalpha() and chars[idx + 1].isalpha():
            chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]

    return "".join(chars)


def random_char_insert(text: str, insert_rate: float = 0.03) -> str:
    """Insert random characters at random positions."""
    chars = list(text)
    n_inserts = max(1, int(len(chars) * insert_rate))

    for _ in range(n_inserts):
        idx = random.randint(0, len(chars))
        char = random.choice("abcdefghijklmnopqrstuvwxyz")
        chars.insert(idx, char)

    return "".join(chars)


def synonym_replace(text: str, replace_rate: float = 0.1) -> str:
    """
    Replace words with synonyms from WordNet.
    Tests if model is robust to paraphrasing.
    """
    try:
        from nltk.corpus import wordnet
        import nltk
        nltk.data.find("corpora/wordnet")
    except LookupError:
        import nltk
        nltk.download("wordnet", quiet=True)
        from nltk.corpus import wordnet

    words = text.split()
    n_replace = max(1, int(len(words) * replace_rate))

    indices = random.sample(range(len(words)), min(n_replace, len(words)))

    for idx in indices:
        word = words[idx].lower()
        synsets = wordnet.synsets(word)
        if synsets:
            synonyms = set()
            for syn in synsets[:3]:
                for lemma in syn.lemmas():
                    if lemma.name().lower() != word and "_" not in lemma.name():
                        synonyms.add(lemma.name())
            if synonyms:
                words[idx] = random.choice(list(synonyms))

    return " ".join(words)


def test_adversarial_robustness(
    predict_fn: Callable,
    texts: list[str],
    labels: np.ndarray,
    n_perturbations: int = 3,
    attacks: list[str] = None,
) -> dict:
    """
    Test model robustness against adversarial perturbations.

    Args:
        predict_fn: function(list[str]) → np.array of predictions (0/1)
        texts: Original input texts
        labels: True labels
        n_perturbations: Number of perturbed versions per text
        attacks: List of attack types ("char_swap", "synonym", "char_insert")

    Returns:
        dict with per-attack flip rates and overall robustness score
    """
    if attacks is None:
        attacks = ["char_swap", "synonym", "char_insert"]

    attack_functions = {
        "char_swap": char_swap,
        "synonym": synonym_replace,
        "char_insert": random_char_insert,
    }

    # Get original predictions
    original_preds = predict_fn(texts)
    original_accuracy = np.mean(original_preds == labels)

    results = {
        "original_accuracy": round(float(original_accuracy), 4),
        "n_samples": len(texts),
        "n_perturbations": n_perturbations,
        "attacks": {},
    }

    for attack_name in attacks:
        if attack_name not in attack_functions:
            logger.warning(f"Unknown attack: {attack_name}")
            continue

        attack_fn = attack_functions[attack_name]
        flip_count = 0
        total_attempts = 0

        for _ in range(n_perturbations):
            perturbed_texts = [attack_fn(t) for t in texts]
            perturbed_preds = predict_fn(perturbed_texts)

            flips = original_preds != perturbed_preds
            flip_count += int(np.sum(flips))
            total_attempts += len(texts)

        flip_rate = flip_count / total_attempts
        perturbed_accuracy = 1.0 - flip_rate  # Approximate

        results["attacks"][attack_name] = {
            "flip_rate": round(flip_rate, 4),
            "flips": flip_count,
            "total_attempts": total_attempts,
        }

        logger.info(
            f"  {attack_name}: flip_rate={flip_rate:.4f} "
            f"({flip_count}/{total_attempts} predictions changed)"
        )

    # Overall robustness score (1 - average flip rate)
    avg_flip = np.mean([a["flip_rate"] for a in results["attacks"].values()])
    results["overall_robustness"] = round(1.0 - avg_flip, 4)

    logger.info(f"Overall robustness score: {results['overall_robustness']}")
    return results
