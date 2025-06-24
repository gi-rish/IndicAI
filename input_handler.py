# input_handler.py

import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import queue
import time
from asr_client import transcribe_with_conformer
from whisper_client import transcribe_with_whisper

q = queue.Queue()

def record_audio(filename="input.wav", fs=16000, max_duration=10, silence_duration=3.0, silence_threshold=0.01):
    print("🎙️ Speak now... (Recording will auto-stop after silence or after 10s max)")

    def callback(indata, frames, time_info, status):
        q.put(indata.copy())

    with sd.InputStream(samplerate=fs, channels=1, callback=callback):
        start_time = time.time()
        last_sound_time = start_time
        audio = []

        while True:
            data = q.get()
            audio.append(data)

            volume_norm = np.linalg.norm(data) / len(data)
            if volume_norm > silence_threshold:
                last_sound_time = time.time()

            if time.time() - last_sound_time > silence_duration:
                break
            if time.time() - start_time > max_duration:
                break

    audio_np = np.concatenate(audio, axis=0)
    wav.write(filename, fs, (audio_np * 32767).astype(np.int16))
    print("Audio saved to:", filename)

def get_user_input(mode: str, lang_code: str) -> str:
    if mode == "voice":
        record_audio()
        if lang_code == "nglish":
            result = transcribe_with_whisper("input.wav")
        else:
            result = transcribe_with_conformer("input.wav", lang_code)

        if not result.strip():
            print("[ASR Error]: Empty transcription.")
            return ""

        return result
    else:
        return input("Type your message: ")
