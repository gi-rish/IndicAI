# asr_client.py
import torch
import torchaudio
import time
import logging
from transformers import AutoModel
from huggingface_hub.utils import HfHubHTTPError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asr_client")

# Initialize model as None, will be loaded with retry logic
model = None

def load_model_with_retries(max_retries=5, initial_delay=30):
    global model
    
    if model is not None:
        return model
    
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt+1}/{max_retries}: Loading ASR model")
            model = AutoModel.from_pretrained(
                "ai4bharat/indic-conformer-600m-multilingual", trust_remote_code=True
            )
            logger.info("ASR model loaded successfully")
            return model
        except HfHubHTTPError as e:
            if "429" in str(e):  # Too Many Requests
                logger.warning(f"Hugging Face rate limit hit (429). Attempt {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    logger.info(f"Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                    # Exponential backoff with jitter
                    delay = min(delay * 2, 300)  # Cap at 5 minutes
                else:
                    logger.error(f"Failed to load ASR model after {max_retries} attempts due to rate limiting")
                    raise
            else:
                logger.error(f"Error loading ASR model: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error loading ASR model: {e}")
            raise

# Try to load the model at import time, but don't block if it fails
try:
    model = load_model_with_retries()
except Exception as e:
    logger.warning(f"Initial model loading failed: {e}. Will retry when needed.")



# Map full language names to ISO codes expected by the model
LANG_MAP = {
    "kannada": "kn",
    "hindi": "hi",
    "marathi": "mr",
    "english": "en",
    "tamil": "ta"
    # Add more if needed
}


def transcribe_audio(file_path: str, lang_code: str) -> str:
    print (lang_code)
    if lang_code == "en":
        # Use Whisper for English
        return transcribe_with_whisper(file_path)
    else:
        # Use Indic Conformer for regional languages
        return transcribe_with_conformer(file_path, lang_code)

def transcribe_with_whisper(audio_path: str) -> str:
    """
    Transcribe English audio using Whisper model
    """
    try:
        import whisper
        
        # Load a smaller model for faster inference
        logger.info("Loading Whisper model for English transcription")
        whisper_model = whisper.load_model("base")
        
        logger.info(f"Transcribing English audio: {audio_path}")
        result = whisper_model.transcribe(audio_path)
        
        return result["text"]
    except Exception as e:
        logger.error(f"[Whisper Error]: {e}")
        return ""

def transcribe_with_conformer(audio_path: str, user_lang: str) -> str:
    try:
        lang_code = LANG_MAP.get(user_lang.lower())
        if lang_code is None:
            raise ValueError(f"Unsupported language: {user_lang}")

        wav, sr = torchaudio.load(audio_path)
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
            wav = resampler(wav)

        # Ensure model is loaded with retry logic
        global model
        if model is None:
            logger.info("ASR model not loaded yet, attempting to load with retries")
            model = load_model_with_retries()
            
        # Run model inference
        try:
            result = model(wav, lang_code, "ctc")  # Use CTC mode for now
            return result
        except Exception as e:
            # If model fails during inference, try reloading it once
            if "not initialized" in str(e).lower() or model is None:
                logger.warning(f"Model inference failed, attempting to reload model: {e}")
                model = load_model_with_retries()
                result = model(wav, lang_code, "ctc")
                return result
            else:
                raise

    except Exception as e:
        logger.error(f"[ASR Error]: {e}")
        return ""
