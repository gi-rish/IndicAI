# utils/lang_code_map.py

LANG_CODE_MAP = {
    "english": "en",
    "hindi": "hi",
    "marathi": "mr",
    "kannada": "kn",
    "tamil": "ta"
}

def get_lang_code(lang: str) -> str:
    return LANG_CODE_MAP.get(lang.lower(), "en")
