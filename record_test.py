import numpy as np
import sounddevice as sd
import soundfile as sf

SECONDS = 10
SAMPLE_RATE = 16000

print(f"Recording for {SECONDS} seconds... speak now.")
audio = sd.rec(int(SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
sd.wait()

audio = np.squeeze(audio)
sf.write("test.wav", audio, SAMPLE_RATE, format="WAV", subtype="PCM_16")
print("Saved test.wav")