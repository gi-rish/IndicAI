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
    text_lower = text.lower()
    text_words = text_lower.split()
    
    # Define common words/patterns for each language to help with transliteration detection
    language_indicators = {
        "hindi": ["mujhe", "kitna", "kya", "hai", "aap", "tum", "kaise", "kab", "kyun", "kaun", "kahan", "yeh", "woh", "main", "hum", "milega", "chahiye", "hua"],
        "kannada": ["neevu", "hegiddira", "nanu", "nanna", "nim", "yenu", "ella", "beku", "illa", "illi", "anta", "ashtu", "ide"],
        "tamil": ["neenga", "eppadi", "enna", "enaku", "unaku", "naan", "romba", "illa", "inge", "ange", "konjam", "venum"],
        "marathi": ["tumhi", "kasa", "kay", "aahe", "mala", "tula", "mi", "amhi", "ithe", "tithe", "pahije"],
        "english": ["how", "what", "when", "where", "why", "who", "will", "can", "could", "would", "should", "is", "are", "am", "get", "have", "much", "loan", "amount", "i", "you", "he", "she", "they", "we", "it", "this", "that", "these", "those"]
    }
    
    # Check if text is in Latin script (transliterated)
    is_latin_script = all(ord(c) < 128 for c in text if c.isalpha())
    
    # First check for English text patterns
    if is_latin_script:
        # Strong indicators for English
        starts_with_english_question = any(text_lower.startswith(word) for word in ["how", "what", "when", "where", "why", "who"])
        english_words = language_indicators["english"]
        english_word_count = sum(1 for word in text_words if word in english_words)
        english_word_ratio = english_word_count / len(text_words) if text_words else 0
        
        # If text starts with English question word or has high ratio of English words
        if starts_with_english_question or english_word_ratio > 0.5:
            print(f"[Detected Language]: english (word pattern analysis)")
            return "english"
    
    # Check for direct language indicators in the text
    language_scores = {}
    for lang, indicators in language_indicators.items():
        if lang == "english":  # Skip English as we've already checked it
            continue
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
        # Connect to local ChromaDB server
        client = chromadb.HttpClient(host="localhost", port=8001)
        collection = client.get_or_create_collection("language_embeddings")
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        embedding = embedder.encode([text])[0]
        
        # Get top 3 results to improve detection accuracy
        result = collection.query(query_embeddings=[embedding], n_results=3)
        if result and result["metadatas"]:
            # Get the top detected language
            lang = result["metadatas"][0][0]["lang"]
            print("[Detected Language]:", lang)
            
            # Double-check with embedding results
            # If the top detected language is English and we've already checked for English patterns
            # in the first part of the function, we can be confident it's English
            if lang == "english":
                print("[Confirmed Language]: english (embedding match)")
                return "english"
                
            # For Hindi text in Devanagari script
            if not all(ord(c) < 128 for c in text if c.isalpha()):
                # If detected as Hindi and contains Devanagari characters
                if lang == "hindi":
                    print("[Confirmed Language]: hindi (Devanagari script)")
                    return "hindi"
                # Return whatever language was detected for non-Latin script
                return lang
            
            # For transliterated text (Latin script)
            # Get all detected languages from top 3 results
            detected_langs = [result["metadatas"][0][i]["lang"] for i in range(min(3, len(result["metadatas"][0])))]            
            print(f"[Top 3 detected languages]: {detected_langs}")
            
            # Enhanced detection for transliterated Hindi
            hindi_indicators = language_indicators["hindi"]
            has_hindi_words = any(word in text_lower for word in hindi_indicators)
            
            # If text contains Hindi indicators or was detected as Tamil but has Hindi words
            if has_hindi_words or (lang == "tamil" and any(word in text_lower for word in hindi_indicators)):
                print("[Language Correction]: Text contains Hindi words, setting to Hindi transliteration")
                return "hindi transliteration"
            
            # Final check for English
            english_indicators = language_indicators["english"]
            has_english_words = any(word in text_lower.split() for word in english_indicators)
            if has_english_words and "english" in detected_langs:
                print("[Language Correction]: Text contains English words and English is in top results")
                return "english"
                
            # For other languages, mark as transliterated
            if lang != "english":
                print(f"[Detected Language]: {lang} (transliterated text)")
                return f"{lang} transliteration"
            
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