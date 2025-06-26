from geminiClient import get_gemini_response

LANG_NAME_MAP = {
    "hi": "Hindi",
    "kn": "Kannada",
    "mr": "Marathi",
    "ta": "Tamil",
    "en": "English"
}
def translate_to_english(text, source_lang_code):
    if source_lang_code == "en":
        return text
    try:
        prompt = (
            f"Translate the following {source_lang_code} sentence to English ONLY.\n"
            f"Do not explain. Do not add context. Just return the translated sentence:\n\n{text}"
        )
        translated = get_gemini_response(prompt)
        print(f"[Gemini → English] {text} → {translated}")
        return translated.strip()
    except Exception as e:
        print(f"Gemini translation to English failed: {e}")
        return text

def translate_back(text, target_lang_code):
    if target_lang_code == "en":
        return text
    try:
        lang_name = LANG_NAME_MAP.get(target_lang_code, target_lang_code)
        prompt = (
            f"Translate the following English sentence to {lang_name} ONLY.\n"
            f"Do not explain. Do not add context. Just return the translated sentence:\n\n{text}"
        )
        translated = get_gemini_response(prompt)
        print(f"[Gemini ← English] {text} → {translated}")
        return translated.strip()
    except Exception as e:
        print(f"Gemini translation back to {target_lang_code} failed: {e}")
        return text