"""Rules-based ESI triage engine. Pure functions, no IO."""

import re
from typing import Optional

from app.schemas import TriageResult

# ESI 1: Life-threatening. Immediate resuscitation.
# Pattern -> human-readable flag for output
ESI_1_PATTERNS: list[tuple[str, str]] = [
    (r"\bnot\s+breathing\b", "not breathing"),
    (r"\bstopped\s+breathing\b", "stopped breathing"),
    (r"\bunresponsive\b", "unresponsive"),
    (r"\bcpr\b", "CPR"),
    (r"\bno\s+pulse\b", "no pulse"),
    (r"\bcardiac\s+arrest\b", "cardiac arrest"),
]

# ESI 2: High acuity. Needs urgent evaluation.
ESI_2_PATTERNS: list[tuple[str, str]] = [
    (r"\bchest\s+pain\b", "chest pain"),
    (r"\bcan'?t\s+breathe\b", "can't breathe"),
    (r"\bcannot\s+breathe\b", "can't breathe"),
    (r"\bdifficulty\s+breathing\b", "difficulty breathing"),
    (r"\bsevere\s+bleeding\b", "severe bleeding"),
    (r"\bheavy\s+bleeding\b", "severe bleeding"),
    (r"\boverdose\b", "overdose"),
    (r"\bsuicidal\b", "suicidal"),
    (r"\bwant\s+to\s+die\b", "suicidal ideation"),
    (r"\bseizure\b", "seizure"),
    (r"\bstroke\b", "stroke"),
    (r"\bpassed\s+out\b", "passed out"),
    (r"\bfainted\b", "fainted"),
    (r"\bhead\s+injury\b", "head injury"),
    (r"\bhead\s+trauma\b", "head injury"),
    (r"\bsevere\s+allergic\s+reaction\b", "severe allergic reaction"),
    (r"\banaphylax", "anaphylaxis"),
    (r"\bchoking\b", "choking"),
]

# Pain scale: severe (9-10) -> ESI 2
SEVERE_PAIN_PATTERN = re.compile(
    r"(?:pain|hurt)\s*(?:is\s*)?(?:9|10)\s*(?:out\s+of\s+10|/\s*10)|"
    r"(?:9|10)\s*(?:out\s+of\s+10|/\s*10)\s*(?:pain|hurt)|"
    r"\bsevere\s+pain\b"
)

# Pain scale: moderate (5-8) -> ESI 3
MODERATE_PAIN_PATTERN = re.compile(
    r"(?:pain|hurt)\s*(?:is\s*)?[5-8]\s*(?:out\s+of\s+10|/\s*10)|"
    r"[5-8]\s*(?:out\s+of\s+10|/\s*10)\s*(?:pain|hurt)|"
    r"\bmoderate\s+(?:pain|headache)\b"
)

# Mild pain (1-4) -> ESI 4
MILD_PAIN_PATTERN = re.compile(
    r"(?:pain|hurt)\s*(?:is\s*)?[1-4]\s*(?:out\s+of\s+10|/\s*10)|"
    r"[1-4]\s*(?:out\s+of\s+10|/\s*10)\s*(?:pain|hurt)|"
    r"\bmild\s+(?:pain|headache|stomach)\b"
)

# High fever 104+ -> ESI 2
HIGH_FEVER_PATTERN = re.compile(
    r"10[4-9]\s*(?:degree|°|F)|1[1-2][0-9]\s*(?:degree|°|F)|"
    r"fever\s+(?:of\s+)?10[4-9]|(?:very\s+)?high\s+fever"
)

# Fever (general) -> ESI 3
FEVER_PATTERN = re.compile(r"\bfever\b|\b101\s+(?:degree|°)|102|103")

# Other ESI 3 indicators: (pattern, label for logging)
ESI_3_INDICATORS: list[tuple[str, str]] = [
    (r"\bvomit(?:ing)?\b", "vomiting"),
    (r"\bthrew\s+up\b", "vomiting"),
    (r"\binjur(?:y|ies)\b", "injury"),
    (r"\bcut\b", "cut"),
    (r"\bbruise\b", "bruise"),
    (r"\bswollen\b", "swelling"),
    (r"\bdizzy\b", "dizziness"),
    (r"\bdizziness\b", "dizziness"),
]

# ESI 4/5: minor
ESI_4_INDICATORS = [
    r"\bsmall\s+cut\b",
    r"\bminor\b",
    r"\bslight\b",
]


def _normalize(text: str) -> str:
    """Lowercase and strip."""
    return (text or "").strip().lower()


def _find_red_flags(text: str) -> list[tuple[int, str]]:
    """Return [(level, flag), ...] for any matched red flags. Level 1 overrides all."""
    text_norm = _normalize(text)
    if not text_norm:
        return []

    found: list[tuple[int, str]] = []

    for pattern, flag in ESI_1_PATTERNS:
        if re.search(pattern, text_norm, re.I):
            found.append((1, flag))

    for pattern, flag in ESI_2_PATTERNS:
        if re.search(pattern, text_norm, re.I):
            found.append((2, flag))

    return found


def _apply_heuristics(text: str) -> tuple[int, list[str]]:
    """
    Apply severity heuristics when no red flags. Returns (esi_level, matched_indicators).
    Conservative: when unclear, assign more urgent (lower number).
    """
    text_norm = _normalize(text)
    if not text_norm:
        return 5, []  # Unclear -> conservative ESI 5

    indicators: list[str] = []

    # ESI 2 heuristics
    if SEVERE_PAIN_PATTERN.search(text_norm):
        indicators.append("severe pain")
        return 2, indicators
    if HIGH_FEVER_PATTERN.search(text_norm):
        indicators.append("high fever")
        return 2, indicators

        # ESI 3 heuristics
    if MODERATE_PAIN_PATTERN.search(text_norm):
        indicators.append("moderate pain")
        return 3, indicators
    if FEVER_PATTERN.search(text_norm):
        indicators.append("fever")
        return 3, indicators

    # --- OPTION 3 OVERRIDE ---
    if re.search(r"\b(?:small|minor|tiny)\s+cut\b", text_norm):
        return 4, ["small/minor cut"]

    for pat, label in ESI_3_INDICATORS:
        if re.search(pat, text_norm):
            indicators.append(label)
            return 3, indicators
            
    # ESI 4 heuristics
    if MILD_PAIN_PATTERN.search(text_norm):
        indicators.append("mild pain")
        return 4, indicators
    for pat in ESI_4_INDICATORS:
        if re.search(pat, text_norm):
            return 4, ["minor symptoms"]

    # ESI 5: unclear or very mild. Conservative -> treat as low acuity but still recommend
    return 5, []


def _build_summary(transcript: str, esi: int, red_flags: list[str]) -> str:
    """One or two sentences summarizing the assessment."""
    transcript = (transcript or "").strip()
    if not transcript:
        return (
            "Based on what you said, we were unable to assess your symptoms. "
            "Consider describing your symptoms in more detail."
        )

    parts = ["Based on what you said, you reported "]
    if red_flags:
        parts.append(", ".join(red_flags))
    else:
        # Truncate long transcript for summary
        snippet = transcript[:100] + "..." if len(transcript) > 100 else transcript
        parts.append(snippet)

    parts.append(".")
    return "".join(parts)


def _build_recommended_action(esi: int) -> str:
    """One sentence recommendation. No diagnosis."""
    if esi == 1:
        return "Call emergency services (e.g., 911) immediately."
    if esi == 2:
        return "Consider seeking emergency care promptly."
    if esi == 3:
        return "Consider seeking urgent care or an emergency department."
    if esi == 4:
        return "Consider calling your doctor or visiting an urgent care when convenient."
    # esi 5
    return "Consider describing your symptoms to a healthcare provider when you can."


def triage_from_transcript(transcript: str) -> TriageResult:
    """
    Run rules-based ESI triage on transcript text.
    Returns a TriageResult. Pure function, no IO.
    """
    text = _normalize(transcript or "")
    red_flag_list = _find_red_flags(transcript or "")

    if red_flag_list:
        # Any ESI 1 -> return 1; else ESI 2
        levels = [level for level, _ in red_flag_list]
        flags = [flag for _, flag in red_flag_list]
        esi = 1 if 1 in levels else 2
        red_flags = list(dict.fromkeys(flags))  # dedupe, preserve order
    else:
        esi, _ = _apply_heuristics(transcript or "")
        red_flags = []

    summary = _build_summary(transcript or "", esi, red_flags)
    recommended_action = _build_recommended_action(esi)

    return TriageResult(
        esi_level=esi,
        red_flags=red_flags,
        summary=summary,
        recommended_action=recommended_action,
    )
