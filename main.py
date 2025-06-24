from input_handler import get_user_input
from asr_client import transcribe_with_conformer
from translator import translate_to_english, translate_back
from llm_client import get_gpt_response
from tts import speak_text

LANG_MAP = {
    "kannada": "kn",
    "hindi": "hi",
    "marathi": "mr",
    "tamil": "ta",
    "english": "en"
}

def main():
    print("Which language would you like to speak in? (e.g., kannada, hindi, marathi, tamil, english): ", end="")
    user_input_lang = input().strip().lower()

    if user_input_lang not in LANG_MAP:
        print("❌ Unsupported language selected.")
        print("Please choose one of the supported languages:", list(LANG_MAP.keys()))
        return

    lang_code = LANG_MAP[user_input_lang]

    print("Choose input mode (text/voice): ", end="")
    input_mode = input().strip().lower()

    chat_history = []

    while True:
        # Step 1: Get user input
        regional_input = get_user_input(input_mode, lang_code)
        if regional_input.strip().lower() in ['exit', 'quit']:
            print("Exiting.")
            break

        # Step 2: Translate to English for LLM
        english_input = translate_to_english(regional_input, lang_code)
        print("[Translated to English]:", english_input)

        # Step 3: LLM interaction
        chat_history.append({"role": "user", "content": english_input})
        reply_english = get_gpt_response(chat_history)
        print("[LLM Reply in English]:", reply_english)

        # Step 4: Translate back to regional
        reply_regional = translate_back(reply_english, lang_code)
        print(f"[Reply in {lang_code.upper()}]:", reply_regional)

        # Step 5: Speak response
        speak_text(reply_regional, lang_code)

        # Step 6: Append to chat history
        chat_history.append({"role": "assistant", "content": reply_english})

if __name__ == "__main__":
    main()
