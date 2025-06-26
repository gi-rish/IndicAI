from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import tempfile
from lang_identifier import get_response, detect_language, transcribe # import as needed

app = FastAPI()

@app.post("/process-input")
async def process_input(
    input_type: str = Form(...),
    input_text: str = Form(None),
    audio_file: UploadFile = Form(None)
):
    chat_history = []

    try:
        audio_path = None
        if input_type == "text":
            if not input_text:
                return JSONResponse(content={"error": "Text input missing"}, status_code=400)

        elif input_type == "voice":
            if not audio_file:
                return JSONResponse(content={"error": "No audio file provided"}, status_code=400)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(await audio_file.read())
                tmp.flush()
                audio_path = tmp.name

            input_text = transcribe(audio_path)  # ✅ Pass path directly


        else:
            return JSONResponse(content={"error": "Invalid input_type"}, status_code=400)

        # ✅ Detect language from text
        detected_lang = detect_language(input_text)

        # ⏬ Pass everything to agent
        result = get_response(
            text=input_text,
            lang=detected_lang,
            chat_history=chat_history,
            audio_file_path=audio_path,
            input_mode=input_type
        )

        return {
            "text_response": result["text_response"],
            "audio_response_path": result["audio_response_path"],
            "english_input":result["english_input"]
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
