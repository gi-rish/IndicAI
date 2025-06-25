from fastapi import FastAPI, Form, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional
import tempfile, json, os

from mcp_context import MCPContext
from pipeline.pipeline_runner import pipeline

app = FastAPI()

@app.post("/process-input")
async def process_input(
    input_type: str = Form(...),                    # "text" or "voice"
    input_text: Optional[str] = Form(None),         # only for "text"
    audio_file: Optional[UploadFile] = Form(None),  # only for "voice"
    chat_history: Optional[str] = Form("[]")        # JSON string
):
    try:
        audio_path = None

        if input_type == "voice":
            if not audio_file:
                return JSONResponse(content={"error": "No audio provided"}, status_code=400)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(await audio_file.read())
                audio_path = tmp.name
        elif input_type == "text":
            if not input_text:
                return JSONResponse(content={"error": "Text input missing"}, status_code=400)
        else:
            return JSONResponse(content={"error": "Invalid input_type"}, status_code=400)

        # Build context
        ctx = MCPContext(
            input_mode=input_type,
            text=input_text,
            chat_history=json.loads(chat_history),
            audio_file_path=audio_path
        )

        # Run full pipeline
        ctx = pipeline.run(ctx)

        return {
            "lang": ctx.lang,
            "translated_to_english": ctx.translated_to_english,
            "gpt_response": ctx.response,
            "translated_back": ctx.response_translated,
            "audio_response_path": ctx.audio_response_path
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
