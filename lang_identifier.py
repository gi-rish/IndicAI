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
from tts import synthesize_and_save_audio

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
    print(text)
    client = chromadb.HttpClient(host="localhost", port=8002)

    collection = client.get_or_create_collection("language_embeddings")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    embedding = embedder.encode([text])[0]
    result = collection.query(query_embeddings=[embedding], n_results=1)
    if result and result["metadatas"]:
        lang = result["metadatas"][0][0]["lang"]
        print("[Detected Language]:", lang)
        return lang
    return "unknown"

# --------------- Step 4: Response Routing ----------------
def get_response(text, lang, chat_history, audio_file_path=None, input_mode="text"):
    if lang == "english":
        print("[Using GPT for response]")
        chat_history.append({"role": "user", "content": text})
        reply = get_gpt_response(chat_history)
        chat_history.append({"role": "assistant", "content": reply})

        audio_path = synthesize_and_save_audio(reply, "en")

        return {
            "text_response": reply,
            "audio_response_path": audio_path
        }

    else:
        print("[Using Indic AI for response]")
        lang_code = LANG_CODE_MAP.get(lang, "hi")
        print(lang_code)

        # 🛠️ Decide the regional input: from audio or direct text
        if input_mode == "voice":
            if audio_file_path is None:
                raise ValueError("Audio file path is required for non-English voice mode")
            regional_transcript = transcribe_audio(audio_file_path, lang)
        else:
            regional_transcript = text

        print(f"[Received Regional Text - {lang.upper()}]: {regional_transcript}")
        english_input = translate_to_english(regional_transcript, lang_code)
        print("[Translated to English]:", english_input)

        chat_history.append({"role": "user", "content": english_input})
        reply_english = get_gpt_response(chat_history)
        chat_history.append({"role": "assistant", "content": reply_english})

        reply_regional = translate_back(reply_english, lang_code)
        print(f"[Translated to {lang.upper()}]:", reply_regional)

        audio_path = synthesize_and_save_audio(reply_regional, lang_code)

        return {
            "text_response": reply_regional,
            "audio_response_path": audio_path
        }



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

        detected_lang = detect_language(input_text)
        audio_file_path = "input.wav" if mode == "voice" else None
        response = response = get_response(
    text=input_text,
    lang=detected_lang,
    chat_history=chat_history,
    input_mode="text"  
)

        print(f"\n💬 [Final Response in {detected_lang.upper()}]: {response}\n")

        lang_code = LANG_CODE_MAP.get(detected_lang, "en")
        speak_text(response, lang_code)

if __name__ == "__main__":
    main()