import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    raise RuntimeError("Missing ELEVENLABS_API_KEY. Put it in .env")

client = ElevenLabs(api_key=api_key)

with open("test.wav", "rb") as f:
    transcription = client.speech_to_text.convert(
        file=f,
        model_id="scribe_v2",
        language_code="eng",
        diarize=False,
        tag_audio_events=False,
    )

text = getattr(transcription, "text", None)
print("\n--- TRANSCRIPT ---")
print(text if text else transcription)