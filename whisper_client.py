import whisper

model = whisper.load_model("base")  # or "small", "medium"

def transcribe_with_whisper(audio_path: str) -> str:
    try:
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        print("[Whisper Error]:", e)
        return ""
