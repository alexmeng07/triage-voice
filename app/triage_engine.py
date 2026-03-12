"""Hybrid triage engine: deterministic rules for ESI 1/2, ML for ESI 3/4/5.

Drop-in replacement for calling triage_rules.triage_from_transcript() directly.
Falls back to the pure rules engine when ML artifacts are not yet trained.
"""

from __future__ import annotations

import logging
from typing import Tuple

from app.schemas import TriageResult
from app.triage_rules import (
    _check_esi_1,
    _check_esi_2,
    _build_summary,
    _build_recommended_action,
    _extract_reported_symptoms,
    triage_from_transcript,
)
from app import ml_model

logger = logging.getLogger(__name__)

# Closeness-based soft up-triage: if the model predicts 4 or 5 but P(3) is
# within this margin of the winning class probability, override to 3.
UP_TRIAGE_MARGIN = 0.10


def _apply_up_triage_bias(probas: dict[int, float]) -> Tuple[int, float]:
    """Apply conservative up-triage bias toward higher acuity.

    Returns (final_label, confidence_for_that_label).
    """
    pred = max(probas, key=probas.get)
    p_pred = probas[pred]
    p3 = probas.get(3, 0.0)

    if pred in (4, 5) and p3 >= p_pred - UP_TRIAGE_MARGIN:
        return 3, p3

    return pred, p_pred


def triage(text: str) -> TriageResult:
    """Run hybrid triage: rules for ESI 1/2, ML classifier for ESI 3/4/5.

    If the ML model is not available (artifacts missing), falls back to the
    pure rule-based engine with a logged warning.
    """
    # STEP 1 -- deterministic rules for life-threatening conditions
    esi1_flags = _check_esi_1(text)
    if esi1_flags:
        return TriageResult(
            esi_level=1,
            red_flags=esi1_flags,
            summary=_build_summary(text, 1, esi1_flags),
            recommended_action=_build_recommended_action(1),
            method="rule",
        )

    # STEP 2 -- deterministic rules for high-risk situations
    esi2_flags = _check_esi_2(text)
    if esi2_flags:
        return TriageResult(
            esi_level=2,
            red_flags=esi2_flags,
            summary=_build_summary(text, 2, esi2_flags),
            recommended_action=_build_recommended_action(2),
            method="rule",
        )

    # STEP 3 -- ML classification for ESI 3/4/5
    try:
        probas = ml_model.predict_proba(text)
    except FileNotFoundError:
        logger.warning(
            "ML artifacts missing -- falling back to rule-based triage. "
            "Run `python -m training.train_esi345` to enable ML."
        )
        return triage_from_transcript(text)

    esi, confidence = _apply_up_triage_bias(probas)
    detected = _extract_reported_symptoms(text)

    return TriageResult(
        esi_level=esi,
        red_flags=detected,
        summary=_build_summary(text, esi, detected),
        recommended_action=_build_recommended_action(esi),
        confidence=confidence,
        method="ml",
    )
