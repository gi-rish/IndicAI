from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import requests
import tempfile
import os

from lang_identifier import transcribe, detect_language
from translator import translate_to_english, translate_back
from llm_client import get_gpt_response
from asr_client import transcribe_audio
from tts import synthesize_and_save_audio

LANG_CODE_MAP = {
    "english": "en",
    "hindi": "hi",
    "kannada": "kn",
    "marathi": "mr",
    "tamil": "ta",
}

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatMessage(BaseModel):
    role: str
    content: str

class TranslationInput(BaseModel):
    text: Optional[str] = None
    audio_url: Optional[str] = None
    target_lang: Optional[str] = "en"
    chat_history: Optional[List[ChatMessage]] = []

class TranslationRequest(BaseModel):
    tool: str
    type: str
    input: TranslationInput

@app.post("/translate")
async def handle_translate(req: TranslationRequest):
    input_data = req.input
    text = input_data.text
    audio_url = input_data.audio_url
    chat_history = input_data.chat_history or []

    # Transcribe if audio is provided
    if audio_url:
        try:
            headers = {
            "User-Agent": "Mozilla/5.0"
            }
            response = requests.get(audio_url, headers=headers, allow_redirects=True)
            if response.status_code != 200:
                raise ValueError("Failed to fetch audio file")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(response.content)
                tmp_file.flush()
                audio_path = tmp_file.name
            input_text = transcribe(audio_path)
            os.remove(audio_path)
            input_mode = "voice"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Audio processing failed: {e}")
    elif text:
        input_text = text
        input_mode = "text"
    else:
        raise HTTPException(status_code=400, detail="Either 'text' or 'audio_url' must be provided")

    # Detect language
    detected_lang = detect_language(input_text)
    lang_code = LANG_CODE_MAP.get(detected_lang.lower(), "en")

    # If English, go direct to GPT
    if detected_lang == "english":
        chat_history.append({"role": "user", "content": input_text})
        reply = get_gpt_response(chat_history)
        chat_history.append({"role": "assistant", "content": reply})
        audio_path = synthesize_and_save_audio(reply, lang_code)
        audio_url = f"http://localhost:8000{audio_path}"

        return {
            "tool": req.tool,
            "type": req.type,
            "input": {
                "text": input_text,
                "audio_url": input_data.audio_url,
                "target_lang": lang_code,
                "detected_lang": "english",
                "translated_text": reply,
                "english_input": input_text,
                "audio_response_path": audio_url
            }
        }

    # Else translate → GPT → translate back
    if input_mode == "voice":
        regional_text = transcribe_audio(audio_path, detected_lang)
    else:
        regional_text = input_text

    english_input = translate_to_english(regional_text, lang_code)
    chat_history.append({"role": "user", "content": english_input})
    reply_english = get_gpt_response(chat_history)
    chat_history.append({"role": "assistant", "content": reply_english})
    reply_regional = translate_back(reply_english, lang_code)

    audio_path = synthesize_and_save_audio(reply_regional, lang_code)
    audio_url = f"http://localhost:8000{audio_path}"

    return {
        "tool": req.tool,
        "type": req.type,
        "input": {
            "text": regional_text,
            "audio_url": input_data.audio_url,
            "target_lang": lang_code,
            "detected_lang": detected_lang,
            "english_input": english_input,
            "translated_text": reply_regional,
            "audio_response_path": audio_url
        }
    }
