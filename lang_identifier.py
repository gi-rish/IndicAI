import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import queue
import time
import unicodedata

from whisper import load_model
from sentence_transformers import SentenceTransformer
import chromadb
from indic_transliteration.sanscript import transliterate
from llm_client import get_gpt_response
from asr_client import transcribe_audio
from translator import  translate_to_english,translate_back
from tts import speak_text

# Language name to code mapping (for Indic AI / translation)
LANG_CODE_MAP = {
    "english": "en",
    "hindi": "hi",
    "kannada": "kn",
    "marathi": "mr",
    "tamil": "ta",
    # Add more as needed
}

# --------------- Step 0: Helpers ----------------
def is_latin(text):
    for ch in text:
        if ch.isalpha() and 'LATIN' not in unicodedata.name(ch, ''):
            return False
    return True

# --------------- Step 1: Record ----------------
def record_audio(filename="input.wav", fs=16000):
    print("Recording...")
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
            if time.time() - last_sound > 2 or time.time() - start > 10:
                break

    audio_np = np.concatenate(audio, axis=0)
    wav.write(filename, fs, (audio_np * 32767).astype(np.int16))
    print("Saved:", filename)

# --------------- Step 2: Transcribe + Transliterate ----------------
def transcribe(file_path="input.wav"):
    model = load_model("base")
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
    client = chromadb.HttpClient(host="localhost", port=8000)
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
def get_response(text, lang):
    if lang == "english":
        print("[Using GPT for response]")
        return get_gpt_response([{"role": "user", "content": text}])
    else:
        print("[Using Indic AI for response]")
        lang_code = LANG_CODE_MAP.get(lang, "en")
        regional_transcript = transcribe_audio("input.wav", lang)
        print("[Regional Transcription]:", regional_transcript)
        english_input = translate_to_english(regional_transcript, lang_code)
        print("[Translated to English]:", english_input)
        # Step 2: Pass to GPT in English
        reply_english = get_gpt_response([{"role": "user", "content": english_input}])

        # Step 3: Translate back to original regional language
        reply_regional = translate_back(reply_english, lang_code)
        print(f"[Translated to {lang.upper()}]:", reply_regional)

        return reply_regional
# --------------- Step 5: Main Flow ----------------
def main():
    record_audio()
    input_text = transcribe()
    detected_lang = detect_language(input_text)

    response = get_response(input_text, detected_lang)
    print(f"[Response in {detected_lang.upper()}]:", response)

    lang_code = LANG_CODE_MAP.get(detected_lang, "en")
    speak_text(response, lang_code)

if __name__ == "__main__":
    main()
