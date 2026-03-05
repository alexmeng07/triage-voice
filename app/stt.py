"""Shared Speech-to-Text helpers (ElevenLabs Scribe v2).

Used by both the CLI and the FastAPI API so transcription logic is not
duplicated.
"""

from __future__ import annotations

import io
import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()


def _get_client() -> ElevenLabs:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing ELEVENLABS_API_KEY. Set it in .env or as an environment variable."
        )
    return ElevenLabs(api_key=api_key)


def transcribe_wav_bytes(wav_bytes: bytes, filename: str = "upload.wav") -> str:
    """Transcribe raw audio bytes via ElevenLabs STT.

    Raises ``RuntimeError`` if the API key is missing or the STT call fails.
    """
    client = _get_client()
    buf = io.BytesIO(wav_bytes)
    buf.name = filename
    transcription = client.speech_to_text.convert(
        file=buf,
        model_id="scribe_v2",
        language_code="eng",
        diarize=False,
        tag_audio_events=False,
    )
    return getattr(transcription, "text", None) or str(transcription)


def transcribe_wav_file(path: str) -> str:
    """Convenience: read a WAV file from disk and transcribe it."""
    with open(path, "rb") as f:
        return transcribe_wav_bytes(f.read(), filename=os.path.basename(path))
