# utils/tts_engine.py

from gtts import gTTS
import os
import uuid

def generate_speech(text, lang_code):
    try:
        lang_map = {
            "english": "en",
            "hindi": "hi",
            "kannada": "kn",
            "marathi": "mr",
            "tamil": "ta"
        }
        lang = lang_map.get(lang_code.lower(), "en")
        filename = f"output_{uuid.uuid4()}.mp3"
        output_path = os.path.join("output", filename)
        os.makedirs("output", exist_ok=True)

        tts = gTTS(text=text, lang=lang)
        tts.save(output_path)
        return output_path

    except Exception as e:
        print(f"[TTS Error]: {e}")
        return None
