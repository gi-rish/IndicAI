# utils/translation.py

from deep_translator import GoogleTranslator
from utils.lang_code_map import get_lang_code

def translate_to_english(text: str, src_lang: str = "auto") -> str:
    try:
        return GoogleTranslator(source=src_lang, target="en").translate(text)
    except Exception as e:
        print(f"[Translation → EN Error]: {e}")
        return text

def translate_from_english(text: str, target_lang: str) -> str:
    try:
        return GoogleTranslator(source="en", target=target_lang).translate(text)
    except Exception as e:
        print(f"[Translation ← EN Error]: {e}")
        return text
