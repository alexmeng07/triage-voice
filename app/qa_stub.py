"""Stub for future health Q&A via LLM. Currently returns a static message."""

from __future__ import annotations


def answer_health_question(question: str) -> str:
    """Return a placeholder answer for health-related questions."""
    base_message = (
        "Planned feature: connect to an LLM API for common health questions.\n"
        "This tool does not provide medical advice. Consult a healthcare professional."
    )
    if not question:
        return base_message
    return f"Question: {question}\n\n{base_message}"

