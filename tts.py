# tts.py

from gtts import gTTS
import os
import playsound
import uuid

def speak_text(text, lang_code):
    try:
        # gTTS supports ISO 639-1 codes, map regional lang_code if needed
        lang_map = {
            "english": "en",
            "hindi": "hi",
            "kannada": "kn",
            "marathi": "mr"
        }
        lang = lang_map.get(lang_code.lower(), "en")


        tts = gTTS(text=text, lang=lang)
        filename = f"temp_{uuid.uuid4()}.mp3"
        tts.save(filename)
        playsound.playsound(filename)
        os.remove(filename)

    except Exception as e:
        print(f"[TTS Error]: {e}")
