"""Interactive terminal interview for triage. Handles I/O and builds TriageCase."""

from __future__ import annotations

from typing import Tuple

from app.triage_note import TriageCase, case_to_note


def _ask(prompt: str) -> str:
    """Simple wrapper around input() for easier testing/mocking later."""
    return input(prompt).strip()


def _ask_yes_no(prompt: str) -> bool:
    """Ask a yes/no question and return True for yes."""
    while True:
        answer = _ask(f"{prompt} [y/n]: ").lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer with 'y' or 'n'.")


def run_interview() -> Tuple[TriageCase, str]:
    """
    Run an interactive terminal-based triage interview.

    Returns (TriageCase, standardized_note_text).
    """
    print("--- INTERACTIVE TRIAGE INTERVIEW ---")
    print("You can press Enter to skip questions marked as optional.\n")

    # Age (optional)
    age_str = _ask("Age (years, optional): ")
    age = None
    if age_str:
        try:
            age_val = int(age_str)
            if age_val < 0:
                print("Age cannot be negative. Treating as unknown.")
            else:
                age = age_val
        except ValueError:
            print("Could not parse age. Treating as unknown.")

    # Chief complaint (required)
    complaint = ""
    while not complaint:
        complaint = _ask("Chief complaint / main symptoms (required): ")
        if not complaint:
            print("Please enter a brief description of the main problem.")

    # Onset / duration (optional but encouraged)
    onset = _ask("When did this start? (onset/duration, e.g., '2 hours', 'since yesterday'; optional): ")

    # Severity 0–10 (optional)
    severity = None
    severity_str = _ask("How bad is it on a scale of 0–10? (optional): ")
    if severity_str:
        try:
            sev_val = int(severity_str)
            if 0 <= sev_val <= 10:
                severity = sev_val
            else:
                print("Severity should be between 0 and 10. Treating as unknown.")
        except ValueError:
            print("Could not parse severity. Treating as unknown.")

    # Red flag checklist
    print("\nNow a few safety questions (yes/no).")
    red_flags: list[str] = []

    if _ask_yes_no("Trouble breathing or feeling like you can't breathe?"):
        # Use phrase compatible with existing rules (difficulty breathing / can't breathe).
        red_flags.append("difficulty breathing")

    if _ask_yes_no("Chest pain or pressure?"):
        red_flags.append("chest pain")

    if _ask_yes_no("Severe or uncontrolled bleeding?"):
        red_flags.append("severe bleeding")

    if _ask_yes_no("Fainting, passing out, or unconsciousness?"):
        red_flags.append("passed out")

    if _ask_yes_no("One-sided weakness, face droop, or slurred speech?"):
        red_flags.append("stroke symptoms")

    if _ask_yes_no("Thoughts of self-harm or suicide?"):
        red_flags.append("suicidal thoughts")

    case = TriageCase(
        age=age,
        complaint=complaint,
        onset=onset,
        severity=severity,
        red_flags=red_flags,
    )

    note = case_to_note(case)

    print("\n--- TRIAGE NOTE ---")
    print(note)

    return case, note

