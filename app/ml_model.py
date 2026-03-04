"""ML inference wrapper for ESI 3/4/5 classification.

Designed for easy swap to a transformer-based model later -- only this module
needs to change.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import joblib  # type: ignore[import-untyped]
import numpy as np

_LABEL_CLASSES = [3, 4, 5]


class ESIClassifier:
    """Lazy-loading wrapper around a TF-IDF + LogReg model."""

    def __init__(self, model_dir: str = "artifacts") -> None:
        self._model_dir = Path(model_dir)
        self._vectorizer = None
        self._model = None

    def _load(self) -> None:
        vec_path = self._model_dir / "vectorizer.joblib"
        mod_path = self._model_dir / "model.joblib"
        if not vec_path.exists() or not mod_path.exists():
            raise FileNotFoundError(
                "ML model artifacts not found. "
                "Run python -m training.train_esi345 to generate them."
            )
        self._vectorizer = joblib.load(vec_path)
        self._model = joblib.load(mod_path)

    def _ensure_loaded(self) -> None:
        if self._model is None or self._vectorizer is None:
            self._load()

    def predict_proba(self, text: str) -> dict[int, float]:
        """Return class probabilities as ``{3: p, 4: p, 5: p}``."""
        self._ensure_loaded()
        assert self._vectorizer is not None
        assert self._model is not None
        tfidf = self._vectorizer.transform([text])
        proba = self._model.predict_proba(tfidf)[0]
        classes = list(self._model.classes_)
        return {int(cls): float(proba[i]) for i, cls in enumerate(classes)}

    def predict(self, text: str) -> Tuple[int, float]:
        """Return ``(predicted_label, confidence)`` where confidence is max prob."""
        probas = self.predict_proba(text)
        label = max(probas, key=probas.__getitem__)
        return label, probas[label]


# Module-level singleton for convenience.
_default_classifier = ESIClassifier()


def predict_proba(text: str) -> dict[int, float]:
    """Convenience: call the default classifier's predict_proba."""
    return _default_classifier.predict_proba(text)


def predict(text: str) -> Tuple[int, float]:
    """Convenience: call the default classifier's predict."""
    return _default_classifier.predict(text)
