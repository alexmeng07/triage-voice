"""Data models for triage results. Pure data, no IO."""

from dataclasses import dataclass


@dataclass
class TriageResult:
    """Result of simulated ESI triage on a transcript."""

    esi_level: int  # 1-5
    red_flags: list[str]
    summary: str
    recommended_action: str
    confidence: float | None = None
    method: str = "rule"
    disclaimer: str = (
        "This is a training and documentation aid, not medical advice or a "
        "clinical decision support tool. All triage suggestions must be "
        "reviewed by a qualified clinician before any clinical action is taken."
    )

    def to_dict(self) -> dict:
        """Serialize for API/frontend consumption."""
        return {
            "esi_level": self.esi_level,
            "red_flags": self.red_flags,
            "summary": self.summary,
            "recommended_action": self.recommended_action,
            "confidence": self.confidence,
            "method": self.method,
            "disclaimer": self.disclaimer,
        }
