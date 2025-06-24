from deep_translator import GoogleTranslator

def translate_to_english(text, source_lang_code):
    if source_lang_code == "en":
        return text
    try:
        translated = GoogleTranslator(source=source_lang_code, target="en").translate(text)
        return translated
    except Exception as e:
        print(f"Translation to English failed: {e}")
        return text

def translate_back(text, target_lang_code):
    if target_lang_code == "en":
        return text
    try:
        translated = GoogleTranslator(source="en", target=target_lang_code).translate(text)
        return translated
    except Exception as e:
        print(f"Translation back to {target_lang_code} failed: {e}")
        return text
