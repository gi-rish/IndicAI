from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, validator
import uuid
import os
import io
import tempfile
import speech_recognition as sr
from minio import Minio
from minio.error import S3Error
from typing import Optional
from datetime import timedelta
from gtts import gTTS
from dotenv import load_dotenv
import time
from typing import Optional, Dict, Any

# Import our existing language detection and translation functions
from lang_identifier import detect_language
from translator import translate_to_english, translate_back
from llm_client import get_gpt_response
from tts import speak_text
from gtts import gTTS
import io

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Indic AI Translation API", description="Translation API with voice input support for Indic languages")

# Initialize Minio client (optional)
minio_client = None
USE_MINIO = os.getenv("USE_MINIO", "false").lower() == "true"

if USE_MINIO:
    try:
        # Get MinIO configuration from environment variables
        endpoint = os.getenv("MINIO_ENDPOINT", "localhost")
        port = os.getenv("MINIO_PORT", "9000")
        access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        # Combine endpoint and port
        endpoint_with_port = f"{endpoint}:{port}"
        
        print(f"Connecting to MinIO at {endpoint_with_port} (secure={secure})")
        
        minio_client = Minio(
            endpoint_with_port,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        # Make sure the bucket exists
        bucket_name = os.getenv("MINIO_BUCKET", "indic-ai-audio")
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"Created bucket: {bucket_name}")
        else:
            print(f"Bucket {bucket_name} already exists")
        print("✅ Minio connection successful")
            
    except Exception as e:
        print(f"⚠️ Minio initialization skipped: {e}")
        print("ℹ️ Audio storage will be disabled")
        minio_client = None
else:
    print("ℹ️ Minio integration disabled (set USE_MINIO=true to enable)")
    print("ℹ️ Audio storage will be disabled")

# Define request and response models
class TranslationRequest(BaseModel):
    text: Optional[str] = None
    voiceKey: Optional[str] = None  # MinIO key for voice input
    chat_history: Optional[list] = None
    system_prompt: Optional[str] = """You are an AI assistant for a microfinance loan process system for joint liability groups. Follow these EXACT guidelines:

1. LOAN AMOUNTS (ALWAYS USE THESE EXACT FIGURES):
   - New customers: Rs. 30,000 to Rs. 50,000 only
   - Renewal customers: Up to Rs. 70,000 only

2. ONBOARDING PROCESS (ALWAYS INCLUDE THESE STEPS):
   - Video consent
   - OTP verification
   - Voter ID/PAN capture
   - L1, L2, L3 details submission

3. QUERY TYPES TO HANDLE:
   - Loan origination queries
   - Loan renewal queries
   - Information retrieval queries

Keep answers brief, clear, and tailored to microfinance contexts in rural India. Assume users have limited financial literacy. NEVER provide loan amounts different from those specified above."""
    
    # Use root validator to check if at least one of text or voiceKey is provided
    @validator('voiceKey')
    def check_voice_key(cls, v, values):
        if not v and not values.get('text'):
            raise ValueError('Either text or voiceKey must be provided')
        return v

class TranslationResponse(BaseModel):
    detected_language: str
    translated_text: str
    audio_id: Optional[str] = None
    english_translation: str  # For debugging/verification
    english_response: str  # The English response before translation back
    is_transliteration: bool = False  # Whether the input was transliterated

# Language code mapping
LANG_CODE_MAP = {
    "english": "en",
    "hindi": "hi",
    "kannada": "kn",
    "tamil": "ta",
    "marathi": "mr"
}

def store_audio_in_minio(audio_data, audio_id):
    """Store audio data in Minio and return success status"""
    if not USE_MINIO or not minio_client:
        return False
    
    try:
        bucket_name = os.getenv("MINIO_BUCKET", "indic-ai-audio")
        object_name = f"{audio_id}.wav"
        
        # Convert audio data to bytes stream
        audio_stream = io.BytesIO(audio_data)
        audio_stream.seek(0)
        
        # Upload to Minio
        minio_client.put_object(
            bucket_name,
            object_name,
            audio_stream,
            length=len(audio_data),
            content_type="audio/wav"
        )
        
        print(f"Audio stored in Minio: {object_name}")
        return True
    except Exception as e:
        print(f"Error storing audio in Minio: {e}")
        return False

def synthesize_speech(text, lang_code):
    """Generate audio data for the given text and language code"""
    try:
        # gTTS supports ISO 639-1 codes, map regional lang_code if needed
        lang_map = {
            "english": "en",
            "hindi": "hi",
            "kannada": "kn",
            "marathi": "mr",
            "tamil": "ta"
        }
        lang = lang_map.get(lang_code.lower(), lang_code)
        
        # Create gTTS object
        tts = gTTS(text=text, lang=lang)
        
        # Save to in-memory buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        return audio_buffer.read()
    except Exception as e:
        print(f"[TTS Error]: {e}")
        return None

def process_audio(text, lang_code, audio_id=None):
    """Generate audio for the translated text and store it in Minio"""
    try:
        # Use provided audio_id or generate a new one
        if audio_id is None:
            audio_id = str(uuid.uuid4())
        
        # Generate audio data
        audio_data = synthesize_speech(text, lang_code)
        
        # Store audio in Minio
        if audio_data:
            success = store_audio_in_minio(audio_data, audio_id)
            if success:
                print(f"Successfully stored audio with ID: {audio_id}")
                return audio_id
            else:
                print(f"Failed to store audio with ID: {audio_id}")
                return None
        return None
    except Exception as e:
        print(f"Error processing audio: {e}")
        return None


def transcribe_audio_from_minio(voice_key):
    """Retrieve audio file from MinIO and transcribe it to text"""
    if not USE_MINIO or not minio_client:
        raise HTTPException(status_code=500, detail="MinIO not configured or unavailable")
    
    try:
        bucket_name = os.getenv("MINIO_BUCKET", "indic-ai-audio")
        
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            temp_path = temp_audio_file.name
            
            # Get the audio file from MinIO
            try:
                response = minio_client.get_object(bucket_name, f"{voice_key}.wav")
                data = response.read()
                temp_audio_file.write(data)
                temp_audio_file.flush()
            except S3Error as e:
                if e.code == "NoSuchKey":
                    raise HTTPException(status_code=404, detail="Voice file not found")
                raise HTTPException(status_code=500, detail=f"Error retrieving voice file: {str(e)}")
        
        # Initialize speech recognizer
        recognizer = sr.Recognizer()
        
        # Transcribe the audio file
        with sr.AudioFile(temp_path) as source:
            audio_data = recognizer.record(source)
            
            try:
                # First try to recognize with Google (requires internet)
                text = recognizer.recognize_google(audio_data)
                print(f"[Voice Transcription]: {text}")
                return text
            except sr.UnknownValueError:
                raise HTTPException(status_code=400, detail="Could not understand audio")
            except sr.RequestError:
                # Fallback to offline recognition if Google API fails
                try:
                    # Use Sphinx for offline recognition
                    text = recognizer.recognize_sphinx(audio_data)
                    print(f"[Voice Transcription (Fallback)]: {text}")
                    return text
                except:
                    raise HTTPException(status_code=400, detail="Failed to transcribe audio")
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error processing voice input: {str(e)}")
        raise e
    finally:
        # Clean up the temporary file
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)

@app.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest, background_tasks: BackgroundTasks):
    """
    Translate text or voice input to English, generate a response, and translate back to the original language.
    Also generates audio for the translated response and stores it in Minio.
    """
    try:
        # Handle voice input if provided
        if request.voiceKey and not request.text:
            try:
                # Transcribe audio from MinIO
                request.text = transcribe_audio_from_minio(request.voiceKey)
                print(f"[Voice Input]: Successfully transcribed voice input: '{request.text}'")
            except HTTPException as e:
                raise e
        
        # Detect language with special handling for transliterated text
        detected_lang = detect_language(request.text)
        
        # Check if it's a transliteration detection
        is_transliteration = False
        if "transliteration" in detected_lang:
            is_transliteration = True
            detected_lang = detected_lang.split(" ")[0]  # Extract just the language name
            print(f"[Detected Language]: {detected_lang} (transliterated text)")
        else:
            print(f"[Detected Language]: {detected_lang}")
        
        # Get language code
        lang_code = LANG_CODE_MAP.get(detected_lang, "en")
        print(f"[DEBUG] Using language code for translation: {lang_code}")
        
        # Log additional information for debugging
        if is_transliteration:
            print(f"[DEBUG] Handling transliterated {detected_lang} text in Latin script")
        
        try:
            # Translate to English
            english_text = translate_to_english(request.text, lang_code)
            print(f"[Translated to English]: {english_text}")
        except Exception as e:
            print(f"[Translation Error]: Failed to translate to English: {str(e)}")
            # Return a partial response with the detected language and transcribed text
            return {
                "detected_language": detected_lang,
                "original_text": request.text,
                "translated_text": request.text,  # Return original text if translation fails
                "gpt_response": "Sorry, I couldn't translate your message at this time. Please try again later.",
                "audio_id": None
            }
        
        # Generate response using GPT
        try:
            # First, create a chat history format that GPT can use
            formatted_chat_history = []
            if request.chat_history:
                formatted_chat_history = request.chat_history
            
            # Add the current request to chat history
            formatted_chat_history.append({"role": "user", "content": english_text})
            
            # Get response from GPT
            gpt_response = get_gpt_response(formatted_chat_history)
            print(f"[GPT Response in English]: {gpt_response}")
            
            # Translate GPT response back to original language
            response = translate_back(gpt_response, lang_code)
            print(f"[Response in {detected_lang.upper()}]: {response}")
        except Exception as e:
            print(f"[GPT/Translation Error]: Failed to generate or translate response: {str(e)}")
            # Return a partial response with the detected language and English translation
            return TranslationResponse(
                detected_language=detected_lang,
                translated_text=request.text,  # Return original text if translation fails
                audio_id=None,
                english_translation=english_text,
                english_response="Sorry, I couldn't generate a response at this time.",
                is_transliteration=is_transliteration
            )
        
        # Generate audio in background
        audio_id = None
        if minio_client:
            # Generate ID for client to use later
            audio_id = str(uuid.uuid4())
            # Process audio in background to avoid blocking the API response
            background_tasks.add_task(process_audio, response, lang_code, audio_id)
        
        # Return response
        return TranslationResponse(
            detected_language=detected_lang,
            translated_text=response,
            audio_id=audio_id,
            english_translation=english_text,
            english_response=gpt_response,
            is_transliteration=is_transliteration
        )
        
    except Exception as e:
        print(f"Error in translation API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{audio_id}")
async def get_audio(audio_id: str, wait: bool = False, max_retries: int = 3):
    """Get the URL for the audio file with the given ID
    
    Args:
        audio_id: The ID of the audio file
        wait: If True, wait for the audio to be available (retry a few times)
        max_retries: Maximum number of retries if wait is True
    """
    if not minio_client:
        raise HTTPException(status_code=500, detail="Minio client not initialized")
    
    bucket_name = os.getenv("MINIO_BUCKET", "indic-ai-audio")
    object_name = f"{audio_id}.wav"
    
    # Try to get the audio URL with retries if wait is True
    retries = 0
    while retries <= max_retries:
        try:
            # Check if object exists
            minio_client.stat_object(bucket_name, object_name)
            
            # Generate presigned URL for the object
            url = minio_client.presigned_get_object(
                bucket_name, 
                object_name,
                expires=timedelta(hours=1)
            )
            
            return {"audio_url": url, "status": "ready"}
        except S3Error as e:
            if e.code == "NoSuchKey":
                # Audio might still be processing
                if wait and retries < max_retries:
                    # Wait and retry
                    retries += 1
                    time.sleep(1)  # Wait for 1 second before retrying
                    continue
                else:
                    # Return a status indicating the audio is still processing
                    return {"status": "processing", "message": "Audio is still being processed", "retry_after": 2}
            else:
                # Other S3 errors
                raise HTTPException(status_code=500, detail=f"Error accessing MinIO: {str(e)}")
    
    # If we've exhausted all retries
    raise HTTPException(status_code=404, detail="Audio not found after maximum retries")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if Minio is available
    minio_status = "available" if minio_client else "unavailable"
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "minio": minio_status,
            "translation": "available"
        }
    }

if __name__ == "__main__":
    import uvicorn
    import socket
    
    # Get port from environment or use default
    port = int(os.getenv("API_PORT", "8080"))
    
    # Check if port is available, if not, try to find an available port
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    # Try to find an available port if the specified one is in use
    if is_port_in_use(port):
        print(f"⚠️ Port {port} is already in use")
        for test_port in range(8000, 9000):
            if not is_port_in_use(test_port):
                port = test_port
                print(f"✅ Found available port: {port}")
                break
    
    print(f"🚀 Starting Translation API server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
