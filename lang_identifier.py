import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import queue
import time
import unicodedata

import whisper
from sentence_transformers import SentenceTransformer
import chromadb
from indic_transliteration.sanscript import transliterate
from llm_client import get_gpt_response
from asr_client import transcribe_audio
from translator import translate_to_english, translate_back
from tts import speak_text

# Language name to code mapping (for Indic AI / translation)
LANG_CODE_MAP = {
    "english": "en",
    "hindi": "hi",
    "kannada": "kn",
    "marathi": "mr",
    "tamil": "ta",
}

# --------------- Step 0: Helpers ----------------
def is_latin(text):
    for ch in text:
        if ch.isalpha() and 'LATIN' not in unicodedata.name(ch, ''):
            return False
    return True

# --------------- Step 1: Record ----------------
def record_audio(filename="input.wav", fs=13000, silence_duration=1.5):
    print("Recording... (speak now)")
    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        q.put(indata.copy())

    with sd.InputStream(samplerate=fs, channels=1, callback=callback):
        audio = []
        start = time.time()
        last_sound = start
        while True:
            data = q.get()
            audio.append(data)
            if np.linalg.norm(data) > 0.01:
                last_sound = time.time()
            # ← update here from 0.1 to silence_duration (e.g., 1.5s)
            if time.time() - last_sound > silence_duration or time.time() - start > 10:
                break

    audio_np = np.concatenate(audio, axis=0)
    wav.write(filename, fs, (audio_np * 32767).astype(np.int16))
    print("Saved:", filename)


# --------------- Step 2: Transcribe + Transliterate ----------------
def transcribe(file_path="input.wav"):
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    raw_text = result["text"].strip()
    print("[Transcript]:", raw_text)

    if not is_latin(raw_text):
        try:
            transliterated = transliterate(raw_text, "devanagari", "iast")
            print("[Transliterated]:", transliterated)
            return transliterated
        except Exception as e:
            print("[Transliteration Failed]:", e)
    return raw_text

# --------------- Step 3: Detect Language ----------------
def detect_language(text):
    """Detect language using embeddings and handle transliterated text."""
    # Dictionary of common words/phrases for each language to help with transliterated text
    language_indicators = {
        "hindi": [
            # Common Hindi words in transliteration
            "kitna", "milega", "mujhe", "kaise", "kaisa", "kya", "hai", "hoga", "karenge", "karoge",
            # Time indicators
            "aaj", "kal", "parso", "abhi", "pehle", "baad",
            # Loan-related Hindi terms
            "loan", "amount", "kitne", "rupaye", "paise", "jankari", "kab", "milega", "chahiye",
            # Financial terms that might be used in transliteration
            "disbursement", "hua", "payment", "emi", "byaj", "interest", "account"
        ],
        "kannada": ["nanu", "nanage", "ninna", "hesaru", "beku", "illa", "enu", "yavaga", "hegide", "maadabeku"],
        "tamil": ["enna", "enakku", "ungal", "peyar", "vendum", "illai", "eppozhuthu", "eppadi", "irukkirathu"],
        "marathi": ["kiti", "milel", "mala", "kasa", "kay", "aahe", "hoil", "karanar", "karal", "pahije"]
    }
    
    text_lower = text.lower()
    text_words = text_lower.split()
    
    # Check for transliterated words in each language with improved scoring
    language_scores = {}
    for lang, indicators in language_indicators.items():
        score = sum(1 for word in indicators if word in text_words)
        if score > 0:
            language_scores[lang] = score
    
    # If we found transliterated words, use the language with the highest score
    if language_scores:
        detected_lang = max(language_scores.items(), key=lambda x: x[1])[0]
        print(f"[Detected Language]: {detected_lang} (transliteration heuristic)")
        return detected_lang
    
    # Use embeddings for language detection as requested
    try:
        client = chromadb.HttpClient(host="localhost", port=8000)
        collection = client.get_or_create_collection("language_embeddings")
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        embedding = embedder.encode([text])[0]
        result = collection.query(query_embeddings=[embedding], n_results=1)
        if result and result["metadatas"]:
            lang = result["metadatas"][0][0]["lang"]
            print("[Detected Language]:", lang)
            
            # Special handling for Hindi phrases that might be detected as Tamil
            # Check if text contains common Hindi words but was detected as Tamil
            if lang == "tamil" and any(word in text_lower for word in language_indicators["hindi"]):
                print("[Language Correction]: Detected as Tamil but contains Hindi words, correcting to Hindi")
                return "hindi transliteration"
            
            # Mark transliterated text explicitly
            if all(ord(c) < 128 for c in text):  # If text is in Latin script
                if lang != "english":
                    print(f"[Detected Language]: {lang} (transliterated text)")
                    return f"{lang} transliteration"
            
            # Don't fallback to English for Latin script - it might be transliterated
            return lang
    except Exception as e:
        print(f"[Embedding Detection Error]: {e}")
    
    # Default to English if detection fails
    print("[Detected Language]: english (default)")
    return "english"

# --------------- Step 4: Response Routing ----------------
def get_response(text=None, lang="english", chat_history=None, audio_file_path=None, input_mode="voice"):
    if chat_history is None:
        chat_history = []

    if lang == "english":
        if not text:
            raise ValueError("Text input is required for English")
        
        print("[Using GPT for response]")
        chat_history.append({"role": "user", "content": text})
        reply = get_gpt_response(chat_history)
        chat_history.append({"role": "assistant", "content": reply})
        return reply

    # For non-English languages
    print("[Using Indic AI for response]")
    lang_code = LANG_CODE_MAP.get(lang)

    if not lang_code:
        raise ValueError(f"Unsupported language: {lang}")

    if input_mode == "voice":
        if not audio_file_path:
            raise ValueError("Audio file path is required for voice mode in non-English languages")
        regional_transcript = transcribe_audio(audio_file_path, lang)
        print(f"[Regional Transcription - {lang.upper()}]: {regional_transcript}")
    else:
        if not text:
            raise ValueError("Text input is required in text mode")
        regional_transcript = text
        print(f"[Received Regional Text - {lang.upper()}]: {regional_transcript}")

    # Translate to English
    english_input = translate_to_english(regional_transcript, lang_code)
    print("[Translated to English]:", english_input)

    # Get GPT response
    chat_history.append({"role": "user", "content": english_input})
    reply_english = get_gpt_response(chat_history)
    chat_history.append({"role": "assistant", "content": reply_english})

    # Translate back
    reply_regional = translate_back(reply_english, lang_code)
    print(f"[Translated to {lang.upper()}]:", reply_regional)

    return reply_regional


# --------------- Step 5: Main Flow ----------------
def main():
    chat_history = []
    print("📝 Input mode? (voice/text): ", end="")
    mode = input().strip().lower()

    while True:
        if mode == "voice":
            record_audio()
            input_text = transcribe()
        else:
            print("🔤 Enter your text (or 'exit' to quit): ", end="")
            input_text = input().strip()
            if input_text.lower() in ["exit", "quit"]:
                break

        # Detect language and verify it's correct
        detected_lang = detect_language(input_text)
        print(f"[DEBUG] Detected language: {detected_lang}")
        
        # Get the language code for translation
        lang_code = LANG_CODE_MAP.get(detected_lang, "en")
        print(f"[DEBUG] Using language code for translation: {lang_code}")
        
        # Get response using the detected language
        audio_file_path = "input.wav" if mode == "voice" else None
        response = get_response(
            text=input_text,
            lang=detected_lang,
            chat_history=chat_history,
            input_mode="text"  
        )

        # Display the final response
        print(f"\n💬 [Final Response in {detected_lang.upper()}]: {response}\n")
        
        # Text-to-speech if available
        try:
            speak_text(response, lang_code)
        except Exception as e:
            print(f"[TTS Error]: {e}")


if __name__ == "__main__":
    main()