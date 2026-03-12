import argparse
import re
from pathlib import Path

from dotenv import load_dotenv

from app.schemas import TriageResult
from app.stt import transcribe_wav_file
from app.triage_rules import triage_from_transcript
from app.interview import run_interview
from app.qa_stub import answer_health_question
from app.triage_note import missing_info_hints, triage_note

# Patient registration helpers (new)
from app.database import init_db
from app.patient_repository import create_patient, lookup_patients

load_dotenv()

# Test harness: hardcoded transcripts for sanity-checking without audio
# Format: (transcript, expected_esi, description)
TEST_TRANSCRIPTS = [
    # ESI 1: Life-threatening
    ("Not breathing", 1, "ESI 1 - not breathing"),
    ("He is having a seizure right now", 1, "ESI 1 - active seizure"),
    ("Patient is unresponsive and no pulse", 1, "ESI 1 - cardiac arrest"),
    ("She is choking and turning blue", 1, "ESI 1 - choking with cyanosis"),
    # ESI 2: High-risk
    ("I can't breathe, someone help", 2, "ESI 2 - can't breathe"),
    ("Chest pain, sweating", 2, "ESI 2 - chest pain"),
    ("I had a seizure last week", 2, "ESI 2 - seizure history (not active)"),
    ("My face is drooping and I have slurred speech", 2, "ESI 2 - stroke symptoms"),
    ("I want to kill myself", 2, "ESI 2 - suicidal ideation"),
    ("My 2 week old baby has a fever", 2, "ESI 2 - infant <3mo with fever"),
    ("My newborn has a fever of 101", 2, "ESI 2 - newborn with fever"),
    ("I feel confused and lethargic", 2, "ESI 2 - altered mental status"),
    # ESI 3: 2+ resources or severity backstop
    ("I think I have appendicitis, severe abdominal pain", 3, "ESI 3 - appendicitis (2+ resources)"),
    ("Pain is 10 out of 10 but otherwise fine", 3, "ESI 3 - severity backstop (10/10 pain)"),
    ("Moderate headache, feeling dizzy", 3, "ESI 3 - moderate pain backstop"),
    ("I have abdominal pain since yesterday", 3, "ESI 3 - abdominal pain (2+ resources)"),
    # ESI 4: 1 resource
    ("I have a small laceration on my hand", 4, "ESI 4 - laceration (1 resource)"),
    ("I think I have a UTI", 4, "ESI 4 - UTI (1 resource)"),
    ("I sprained my ankle", 4, "ESI 4 - sprain (1 resource)"),
    ("I have an ear infection", 4, "ESI 4 - ear infection (1 resource)"),
    # ESI 5: 0 resources
    ("I need a medication refill", 5, "ESI 5 - medication refill (0 resources)"),
    ("Just a mild cold", 5, "ESI 5 - mild cold (0 resources)"),
    ("Mild stomach ache", 5, "ESI 5 - mild symptom (0 resources)"),
    ("Hello, I'm not sure what's wrong", 5, "ESI 5 - unclear symptoms"),
]


def record_audio(path: str = "test.wav", seconds: int = 6) -> None:
    import numpy as np
    import sounddevice as sd
    import soundfile as sf

    sample_rate = 16000
    print(f"Recording for {seconds} seconds... speak now.")
    audio = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    audio = np.squeeze(audio)
    sf.write(path, audio, sample_rate, format="WAV", subtype="PCM_16")
    print(f"Saved {path}")


def transcribe_wav(wav_path: str) -> str:
    return transcribe_wav_file(wav_path)


def _highlight_quoted(text: str) -> str:
    """Wrap text inside double quotes with ANSI cyan."""
    CYAN = "\033[36m"
    RESET = "\033[0m"
    return re.sub(r'"([^"]+)"', f'{CYAN}"\\1"{RESET}', text)


def print_result(result: TriageResult) -> None: 
    print("\n--- CHECKPOINT C: TRIAGE RESULT ---")
    print(f"ESI Level: {result.esi_level}")
    if result.method != "rule":
        print(f"Method: {result.method} (confidence: {result.confidence:.0%})")
    print(f"Red flags: {result.red_flags if result.red_flags else '(none)'}")
    print(f"Summary: {_highlight_quoted(result.summary)}")
    print(f"Recommended action: {result.recommended_action}")
    print(f"Disclaimer: {result.disclaimer}")


def run_test_harness() -> None:
    passed = 0
    failed = 0
    for i, (transcript, expected_esi, description) in enumerate(TEST_TRANSCRIPTS, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}/{len(TEST_TRANSCRIPTS)}: {description}")
        print(f"--- TRANSCRIPT ---\n{transcript}")
        result = triage_from_transcript(transcript)
        print_result(result)
        
        status = "PASS" if result.esi_level == expected_esi else "FAIL"
        if result.esi_level == expected_esi:
            passed += 1
        else:
            failed += 1
            print(f"\n*** {status}: Expected ESI {expected_esi}, got ESI {result.esi_level} ***")
    
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY: {passed} passed, {failed} failed out of {len(TEST_TRANSCRIPTS)}")


def run_full(record_first: bool, wav_path: str) -> None:
    if record_first:
        record_audio(wav_path)
    if not Path(wav_path).exists():
        print(f"Error: {wav_path} not found. Use --record to record first.")
        return

    print("\nTranscribing...")
    transcript = transcribe_wav(wav_path)
    print("\n--- TRANSCRIPT ---")
    print(transcript or "(empty)")

    result = triage_note(transcript or "")
    print_result(result)

    hints = missing_info_hints(transcript or "")
    if hints:
        print("\nMissing info (optional, could improve triage):")
        for h in hints:
            print(f"- {h}")


def run_voicemail(audio_path: str) -> None:
    path = Path(audio_path)
    if not path.exists():
        print(f"Error: {audio_path} not found.")
        return

    print("\n--- VOICEMAIL TRIAGE ---")
    print(f"Using audio file: {audio_path}")
    print("\nTranscribing (no follow-up questions)...")
    transcript = transcribe_wav(str(path))

    print("\n--- TRANSCRIPT ---")
    print(transcript or "(empty)")

    result = triage_note(transcript or "")
    print_result(result)

    hints = missing_info_hints(transcript or "")
    if hints:
        print("\nMissing info (optional, could improve triage):")
        for h in hints:
            print(f"- {h}")


def run_dry_run() -> None:
    print("--- DRY-RUN TRIAGE ---")
    transcript = input("Paste transcript text (single line) for triage: ").strip()
    print("\n--- TRANSCRIPT ---")
    print(transcript or "(empty)")

    result = triage_note(transcript or "")
    print_result(result)

    hints = missing_info_hints(transcript or "")
    if hints:
        print("\nMissing info (optional, could improve triage):")
        for h in hints:
            print(f"- {h}")


def run_register_patient() -> None:
    """Interactively register a new patient from the command line."""
    init_db()  # make sure DB exists

    print("\n--- REGISTER NEW PATIENT ---")
    first_name = input("First name: ").strip()
    last_name = input("Last name: ").strip()
    dob = input("Date of birth (YYYY-MM-DD): ").strip()
    phone = input("Phone (optional, press Enter to skip): ").strip() or None
    sex = input("Sex (M/F/O, optional): ").strip() or None
    address = input("Address (optional): ").strip() or None

    if not first_name or not last_name or not dob:
        print("Error: first_name, last_name, and date_of_birth are required.")
        return

    patient = create_patient(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=dob,
        phone=phone,
        sex=sex,
        address=address,
    )
    print(f"\nPatient created successfully!")
    print(f"  ID:    {patient['id']}")
    print(f"  Name:  {patient['first_name']} {patient['last_name']}")
    print(f"  DOB:   {patient['date_of_birth']}")
    print(f"  Phone: {patient['phone'] or '(none)'}")


def run_lookup_patient() -> None:
    """Interactively look up patients from the command line."""
    init_db()  # make sure DB exists

    print("\n--- PATIENT LOOKUP ---")
    print("(Leave fields blank to skip them)")
    first_name = input("First name: ").strip() or None
    last_name = input("Last name: ").strip() or None
    dob = input("Date of birth (YYYY-MM-DD): ").strip() or None
    phone = input("Phone: ").strip() or None

    if not any([first_name, last_name, dob, phone]):
        print("Error: provide at least one search field.")
        return

    matches = lookup_patients(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=dob,
        phone=phone,
    )

    if not matches:
        print("\nNo patients found.")
    else:
        print(f"\nFound {len(matches)} patient(s):")
        for m in matches:
            print(f"  ID {m['id']}: {m['first_name']} {m['last_name']} "
                  f"(DOB: {m['date_of_birth']}, Phone: {m['phone'] or 'N/A'})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Triage-voice Checkpoint C: Record, transcribe, triage (simulation, not medical advice)."
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Record mic to test.wav before transcribing",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test harness with hardcoded transcripts (no mic, no API)",
    )
    parser.add_argument(
        "--voicemail",
        metavar="PATH",
        help="Voicemail-style triage on a prerecorded audio file (e.g., clinic voicemail).",
    )
    parser.add_argument(
        "--interview",
        action="store_true",
        help="Start an interactive text-based triage interview.",
    )
    parser.add_argument(
        "--ask",
        metavar="QUESTION",
        help="Ask a general health-related question (stub; not medical advice).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip audio/STT and enter transcript text manually for triage.",
    )
    parser.add_argument(
        "--wav",
        default="test.wav",
        help="Path to WAV file for record/transcribe mode (default: test.wav)",
    )
    # --- Patient commands (new) ---
    parser.add_argument(
        "--register-patient",
        action="store_true",
        help="Interactively register a new patient in the local database.",
    )
    parser.add_argument(
        "--lookup-patient",
        action="store_true",
        help="Interactively look up a patient in the local database.",
    )
    args = parser.parse_args()

    # Mode precedence: choose a single clear path.
    if args.test:
        run_test_harness()
        return

    if args.ask:
        response = answer_health_question(args.ask)
        print(response)
        return

    if args.interview:
        _, note = run_interview()
        result = triage_note(note)
        print_result(result)

        hints = missing_info_hints(note)
        if hints:
            print("\nMissing info (optional, could improve triage):")
            for h in hints:
                print(f"- {h}")
        return

    if args.dry_run:
        run_dry_run()
        return

    if args.voicemail:
        run_voicemail(args.voicemail)
        return

    if args.register_patient:
        run_register_patient()
        return

    if args.lookup_patient:
        run_lookup_patient()
        return

    # Default: existing record/wav flow.
    run_full(record_first=args.record, wav_path=args.wav)


if __name__ == "__main__":
    main()

