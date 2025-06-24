language_code_map = {
    "hindi": "hi",
    "kannada": "kn",
    "marathi": "mr",
    "english": "en"
}

def get_user_language():
    lang = input("Which language would you like to speak in? (e.g., kannada, hindi, marathi, english): ").lower().strip()
    while lang not in language_code_map:
        lang = input("Unsupported language. Please enter hindi, kannada, marathi, or english: ").lower().strip()
    return language_code_map[lang]