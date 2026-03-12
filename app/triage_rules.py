"""Rules-based ESI triage engine following 4-step ESI algorithm. Pure functions, no IO."""

import re
from typing import List, Tuple

from app.schemas import TriageResult

# =============================================================================
# ESI 1: Life-threatening - Immediate resuscitation required
# =============================================================================

ESI_1_PATTERNS: List[Tuple[str, str]] = [
    (r"\bnot\s+breathing\b", "not breathing"),
    (r"\bstopped\s+breathing\b", "stopped breathing"),
    (r"\bunresponsive\b", "unresponsive"),
    (r"\bcpr\b", "CPR"),
    (r"\bno\s+pulse\b", "no pulse"),
    (r"\bcardiac\s+arrest\b", "cardiac arrest"),
    (r"\bgasping\b", "gasping"),
    (r"\bcyanosis\b", "cyanosis"),
    (r"\bblue\s+lips\b", "blue lips"),
    (r"\bairway\s+swell", "airway swelling"),
    (r"\bsevere\s+respiratory\s+distress\b", "severe respiratory distress"),
    (r"\bmassive\s+bleed", "massive bleeding"),
    (r"\bspurting\s+blood\b", "spurting blood"),
    (r"\bchoking\b", "choking"),
]

ACTIVE_SEIZURE_INDICATORS = [
    r"\bright\s+now\b",
    r"\bcurrently\b",
    r"\bstill\b",
    r"\bactively\b",
    r"\bwon'?t\s+stop\b",
    r"\bhaving\s+a\s+seizure\b",
    r"\bseizing\s+now\b",
]

# =============================================================================
# ESI 2: High-risk situations, altered mental status, severe distress
# =============================================================================

ESI_2_PATTERNS: List[Tuple[str, str]] = [
    # Existing patterns
    (r"\bchest\s+pain\b", "chest pain"),
    (r"\bcan'?t\s+breathe\b", "can't breathe"),
    (r"\bcannot\s+breathe\b", "can't breathe"),
    (r"\bdifficulty\s+breathing\b", "difficulty breathing"),
    (r"\bsevere\s+bleeding\b", "severe bleeding"),
    (r"\bheavy\s+bleeding\b", "severe bleeding"),
    (r"\boverdose\b", "overdose"),
    (r"\bstroke\b", "stroke"),
    (r"\bpassed\s+out\b", "passed out"),
    (r"\bfainted\b", "fainted"),
    (r"\bhead\s+injury\b", "head injury"),
    (r"\bhead\s+trauma\b", "head injury"),
    (r"\bsevere\s+allergic\s+reaction\b", "severe allergic reaction"),
    (r"\banaphylax", "anaphylaxis"),
    # Neurologic/stroke symptoms
    (r"\bface\s+droop", "face droop"),
    (r"\bslurred\s+speech\b", "slurred speech"),
    (r"\bone[- ]?sided\s+weakness\b", "one-sided weakness"),
    (r"\bsudden\s+vision\s+loss\b", "sudden vision loss"),
    # Altered mental status
    (r"\bconfused\b", "confused"),
    (r"\bnot\s+making\s+sense\b", "altered mental status"),
    (r"\blethargic\b", "lethargic"),
    (r"\bdifficult\s+to\s+wake\b", "difficult to wake"),
    # Psychiatric crisis
    (r"\bsuicidal\b", "suicidal"),
    (r"\bwant\s+to\s+(?:die|kill\s+myself)\b", "suicidal ideation"),
    (r"\boverdose\s+attempt\b", "overdose attempt"),
    # Severe asthma
    (r"\binhaler\s+not\s+help", "inhaler not helping"),
    (r"\bsevere\s+wheez", "severe wheezing"),
    # Non-active seizure (history or general mention)
    (r"\bseizure\b", "seizure"),
    # Not feeding (pediatric)
    (r"\bnot\s+feeding\b", "not feeding"),
    (r"\binconsolable\b", "inconsolable crying"),
]

PEDIATRIC_UNDER_3MO_PATTERNS = [
    r"\bnewborn\b",
    r"\bunder\s+3\s+months?\b",
    r"\b(?:2|two)\s+weeks?\s+old\b",
    r"\b(?:6|six)\s+weeks?\s+old\b",
    r"\b(?:1|one)\s+month\s+old\b",
    r"\b(?:2|two)\s+months?\s+old\b",
    r"\b(?:1|one)\s+week\s+old\b",
]

# =============================================================================
# Pain/Distress patterns for severity backstop
# =============================================================================

SEVERE_PAIN_PATTERN = re.compile(
    r"(?:pain|hurt)\s*(?:is\s*)?(?:9|10)\s*(?:out\s+of\s+10|/\s*10)|"
    r"(?:9|10)\s*(?:out\s+of\s+10|/\s*10)\s*(?:pain|hurt)|"
    r"\bsevere\s+pain\b"
)

MODERATE_PAIN_PATTERN = re.compile(
    r"(?:pain|hurt)\s*(?:is\s*)?[5-8]\s*(?:out\s+of\s+10|/\s*10)|"
    r"[5-8]\s*(?:out\s+of\s+10|/\s*10)\s*(?:pain|hurt)|"
    r"\bmoderate\s+(?:pain|headache)\b"
)

MILD_PAIN_PATTERN = re.compile(
    r"(?:pain|hurt)\s*(?:is\s*)?[1-4]\s*(?:out\s+of\s+10|/\s*10)|"
    r"[1-4]\s*(?:out\s+of\s+10|/\s*10)\s*(?:pain|hurt)|"
    r"\bmild\s+(?:pain|headache|stomach)\b"
)

SEVERE_DISTRESS_PATTERN = re.compile(r"\bsevere\s+distress\b")

HIGH_FEVER_PATTERN = re.compile(
    r"10[4-9]\s*(?:degree|°|F)|1[1-2][0-9]\s*(?:degree|°|F)|"
    r"fever\s+(?:of\s+)?10[4-9]|(?:very\s+)?high\s+fever"
)

# =============================================================================
# Resource estimation patterns (Step 3)
# =============================================================================

TWO_PLUS_RESOURCES = [
    (r"\bchest\s+pain\b", "chest pain"),
    (r"\babdominal\s+pain\b", "abdominal pain"),
    (r"\bfracture\b", "fracture"),
    (r"\bhead\s+injury\b", "head injury"),
    (r"\bsevere\s+infection\b", "severe infection"),
    (r"\bkidney\s+stone\b", "kidney stone"),
    (r"\bsevere\s+dehydration\b", "severe dehydration"),
    (r"\bappendic", "possible appendicitis"),
    (r"\bpneumonia\b", "pneumonia"),
    (r"\bbroken\s+bone\b", "broken bone"),
]

ONE_RESOURCE = [
    (r"\blaceration\b", "laceration"),
    (r"\bsimple\s+wound\b", "simple wound"),
    (r"\bsprain(?:ed)?\b", "sprain"),
    (r"\buti\b|\burinary\s+tract\b", "UTI symptoms"),
    (r"\bear\s+infection\b", "ear infection"),
    (r"\bstitches\b", "needs stitches"),
    (r"\bx-?ray\b", "needs x-ray"),
]

ZERO_RESOURCES = [
    (r"\bmedication\s+refill\b", "medication refill"),
    (r"\bmild\s+cold\b", "mild cold"),
    (r"\bminor\s+rash\b", "minor rash"),
    (r"\bsimple\s+sore\s+throat\b", "simple sore throat"),
    (r"\bprescription\s+refill\b", "prescription refill"),
]

# Additional common symptom patterns not covered by the ESI / resource lists
ADDITIONAL_SYMPTOM_PATTERNS: List[Tuple[str, str]] = [
    (r"\bheadache\b", "headache"),
    (r"\bdizz(?:y|iness)\b", "dizziness"),
    (r"\bnausea\b", "nausea"),
    (r"\bvomit(?:ing)?\b", "vomiting"),
    (r"\bcough(?:ing)?\b", "cough"),
    (r"\bback\s+pain\b", "back pain"),
    (r"\bjoint\s+pain\b", "joint pain"),
    (r"\bswell(?:ing|ed|olen)\b", "swelling"),
    (r"\bnumb(?:ness)?\b", "numbness"),
    (r"\btingling\b", "tingling"),
    (r"\bfatigue\b|\bexhausted\b", "fatigue"),
    (r"\bdiarrhea\b", "diarrhea"),
    (r"\bconstipation\b", "constipation"),
    (r"\bfever\b", "fever"),
    (r"\bchills?\b", "chills"),
    (r"\bshortness\s+of\s+breath\b", "shortness of breath"),
    (r"\bblurr(?:y|ed)\s+vision\b", "blurry vision"),
    (r"\btremor\b|\bshaking\b", "tremor"),
    (r"\bpalpitation\b|\bheart\s+racing\b", "palpitations"),
    (r"\bstomach\s*(?:ache|pain)\b", "stomach pain"),
    (r"\bleg\s+pain\b", "leg pain"),
    (r"\bneck\s+pain\b", "neck pain"),
    (r"\bshoulder\s+pain\b", "shoulder pain"),
]


def _normalize(text: str) -> str:
    """Lowercase and strip."""
    return (text or "").strip().lower()


def _check_active_seizure(text: str) -> bool:
    """Check if transcript indicates an ACTIVE seizure happening now."""
    text_norm = _normalize(text)
    has_seizure = bool(re.search(r"\bseiz(?:ure|ing)\b", text_norm, re.I))
    if not has_seizure:
        return False
    for indicator in ACTIVE_SEIZURE_INDICATORS:
        if re.search(indicator, text_norm, re.I):
            return True
    return False


def _check_pediatric_fever(text: str) -> bool:
    """Check if transcript indicates infant <3 months with fever."""
    text_norm = _normalize(text)
    has_fever = bool(re.search(r"\bfever\b", text_norm, re.I))
    if not has_fever:
        return False
    for pattern in PEDIATRIC_UNDER_3MO_PATTERNS:
        if re.search(pattern, text_norm, re.I):
            return True
    return False


def _check_esi_1(text: str) -> List[str]:
    """
    STEP 1: Check for immediate life-threatening conditions requiring resuscitation.
    Returns list of matched flags if ESI 1, empty list otherwise.
    """
    text_norm = _normalize(text)
    if not text_norm:
        return []

    flags: List[str] = []

    if _check_active_seizure(text):
        flags.append("active seizure")

    for pattern, flag in ESI_1_PATTERNS:
        if re.search(pattern, text_norm, re.I):
            flags.append(flag)

    return list(dict.fromkeys(flags))


def _check_esi_2(text: str) -> List[str]:
    """
    STEP 2: Check for high-risk situations, altered mental status, severe distress.
    Returns list of matched flags if ESI 2, empty list otherwise.
    """
    text_norm = _normalize(text)
    if not text_norm:
        return []

    flags: List[str] = []

    if _check_pediatric_fever(text):
        flags.append("infant <3mo with fever")

    if HIGH_FEVER_PATTERN.search(text_norm):
        flags.append("high fever")

    for pattern, flag in ESI_2_PATTERNS:
        if re.search(pattern, text_norm, re.I):
            if flag in ("seizure", "seizing") and _check_active_seizure(text):
                continue
            flags.append(flag)

    return list(dict.fromkeys(flags))


def _has_modifier(text: str, keyword: str, modifier: str) -> bool:
    """Check if a modifier appears near a keyword (within ~30 chars)."""
    text_norm = _normalize(text)
    keyword_match = re.search(keyword, text_norm, re.I)
    if not keyword_match:
        return False
    start = max(0, keyword_match.start() - 30)
    end = min(len(text_norm), keyword_match.end() + 30)
    context = text_norm[start:end]
    return bool(re.search(rf"\b{modifier}\b", context, re.I))


def estimate_resources(text: str) -> Tuple[int, List[str]]:
    """
    STEP 3: Estimate expected resource utilization.
    Returns (resource_count, matched_indicators).
    Applies mild/severe modifiers with conservative bias.
    """
    text_norm = _normalize(text)
    if not text_norm:
        return 0, []

    indicators: List[str] = []
    base_count = 0

    for pattern, label in TWO_PLUS_RESOURCES:
        if re.search(pattern, text_norm, re.I):
            indicators.append(label)
            if _has_modifier(text_norm, pattern, "mild"):
                base_count = max(base_count, 1)
            else:
                base_count = 2
            break

    if base_count == 0:
        for pattern, label in ONE_RESOURCE:
            if re.search(pattern, text_norm, re.I):
                indicators.append(label)
                if _has_modifier(text_norm, pattern, "severe"):
                    base_count = 2
                else:
                    base_count = 1
                break

    if base_count == 0:
        for pattern, label in ZERO_RESOURCES:
            if re.search(pattern, text_norm, re.I):
                indicators.append(label)
                base_count = 0
                break

    if re.search(r"\bsevere\b", text_norm, re.I) and base_count < 2:
        base_count = min(base_count + 1, 2)

    return base_count, indicators


def _apply_severity_backstop(text: str, current_esi: int) -> Tuple[int, List[str]]:
    """
    Apply severity backstop after resource-based ESI assignment.
    Prevents high pain from becoming low-acuity ESI.
    """
    text_norm = _normalize(text)
    flags: List[str] = []
    esi = current_esi

    if SEVERE_DISTRESS_PATTERN.search(text_norm):
        if esi > 2:
            esi = 2
            flags.append("severe distress")
    elif SEVERE_PAIN_PATTERN.search(text_norm):
        if esi > 3:
            esi = 3
            flags.append("severe pain")
    elif MODERATE_PAIN_PATTERN.search(text_norm):
        if esi > 3:
            esi = 3
            flags.append("moderate pain")

    return esi, flags


def _extract_pain_level(text_norm: str) -> int | None:
    """Extract a 0–10 pain or severity score from normalized text."""
    for pattern in [
        r"(?:pain|hurt|severity)\s*(?:is\s*)?(\d{1,2})\s*(?:out\s+of\s+10|/\s*10)",
        r"(\d{1,2})\s*(?:out\s+of\s+10|/\s*10)\s*(?:pain|hurt)",
        r"severity[:\s]+(\d{1,2})/10",
    ]:
        m = re.search(pattern, text_norm)
        if m:
            val = int(m.group(1))
            if 0 <= val <= 10:
                return val
    return None


def _extract_reported_symptoms(text: str) -> List[str]:
    """Extract all clinically relevant symptoms detected in free text.

    Scans ESI patterns, resource patterns, common symptom patterns, and
    pain level.  Returns a deduplicated list ordered by clinical priority:
    critical → high-risk → clinical → general.
    """
    text_norm = _normalize(text)
    if not text_norm:
        return []

    critical: List[str] = []
    high_risk: List[str] = []
    clinical: List[str] = []
    general: List[str] = []
    seen: set = set()

    def _add(label: str, bucket: List[str]) -> None:
        key = label.lower()
        if key not in seen:
            seen.add(key)
            bucket.append(label)

    if _check_active_seizure(text):
        _add("active seizure", critical)

    if _check_pediatric_fever(text):
        _add("infant <3mo with fever", critical)

    for pattern, label in ESI_1_PATTERNS:
        if re.search(pattern, text_norm, re.I):
            _add(label, critical)

    for pattern, label in ESI_2_PATTERNS:
        if re.search(pattern, text_norm, re.I):
            _add(label, high_risk)

    if HIGH_FEVER_PATTERN.search(text_norm):
        _add("high fever", high_risk)

    for pattern, label in TWO_PLUS_RESOURCES + ONE_RESOURCE + ZERO_RESOURCES:
        if re.search(pattern, text_norm, re.I):
            _add(label, clinical)

    for pattern, label in ADDITIONAL_SYMPTOM_PATTERNS:
        if re.search(pattern, text_norm, re.I):
            _add(label, general)

    pain = _extract_pain_level(text_norm)
    if pain is not None:
        _add(f"{pain}/10 pain level", high_risk if pain >= 7 else general)

    return critical + high_risk + clinical + general


def _build_summary(transcript: str, esi: int, red_flags: List[str]) -> str:
    """One or two sentences summarizing the assessment."""
    transcript = (transcript or "").strip()
    if not transcript:
        return (
            "Based on what you said, we were unable to assess your symptoms. "
            "Consider describing your symptoms in more detail."
        )

    symptoms = red_flags if red_flags else _extract_reported_symptoms(transcript)

    if symptoms:
        symptom_text = ", ".join(symptoms)
    else:
        snippet = transcript[:80].rstrip()
        if len(transcript) > 80:
            snippet += "\u2026"
        symptom_text = snippet

    return f'Based on what you said, you reported "{symptom_text}".'


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
    return "Consider describing your symptoms to a healthcare provider when you can."


def triage_from_transcript(transcript: str) -> TriageResult:
    """
    Run 4-step ESI triage algorithm on transcript text.
    
    STEP 1: Immediate life-saving intervention required? -> ESI 1
    STEP 2: High-risk situation, altered mental status, or severe distress? -> ESI 2
    STEP 3: Estimate expected resource utilization
    STEP 4: Assign ESI 3/4/5 based on predicted resource count
    
    Returns a TriageResult. Pure function, no IO.
    """
    text = _normalize(transcript or "")

    # STEP 1: Life-threatening -> ESI 1
    esi1_flags = _check_esi_1(text)
    if esi1_flags:
        return TriageResult(
            esi_level=1,
            red_flags=esi1_flags,
            summary=_build_summary(transcript, 1, esi1_flags),
            recommended_action=_build_recommended_action(1),
        )

    # STEP 2: High-risk -> ESI 2
    esi2_flags = _check_esi_2(text)
    if esi2_flags:
        return TriageResult(
            esi_level=2,
            red_flags=esi2_flags,
            summary=_build_summary(transcript, 2, esi2_flags),
            recommended_action=_build_recommended_action(2),
        )

    # STEP 3: Estimate resources
    resource_count, resource_indicators = estimate_resources(text)

    # STEP 4: Assign ESI 3/4/5 based on resources
    if resource_count >= 2:
        esi = 3
    elif resource_count == 1:
        esi = 4
    else:
        esi = 5

    # Apply severity backstop
    esi, backstop_flags = _apply_severity_backstop(text, esi)
    all_flags = resource_indicators + backstop_flags

    return TriageResult(
        esi_level=esi,
        red_flags=list(dict.fromkeys(all_flags)),
        summary=_build_summary(transcript, esi, all_flags),
        recommended_action=_build_recommended_action(esi),
    )
