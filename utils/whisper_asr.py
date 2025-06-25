# utils/whisper_asr.py
import whisper

model = whisper.load_model("base")  # or "small", "medium", etc.

def transcribe(audio_path: str) -> str:
    result = model.transcribe(audio_path)
    return result.get("text", "")
