# tts.py

from gtts import gTTS
import os
import uuid
import logging

logger = logging.getLogger(__name__)

# No need to try importing playsound in Docker environment
PLAYSOUND_AVAILABLE = False

def speak_text(text, lang_code):
    """
    Convert text to speech for the given language code.
    In Docker environment, this just saves the audio file without playback.
    
    Args:
        text (str): Text to convert to speech
        lang_code (str): Language code or name (e.g., 'en', 'english', 'hi', 'hindi')
        
    Returns:
        str: Filename of the generated audio file or None if failed
    """
    try:
        # gTTS supports ISO 639-1 codes, map regional lang_code if needed
        lang_map = {
            "english": "en",
            "hindi": "hi",
            "kannada": "kn",
            "marathi": "mr",
            "tamil": "ta",
            "telugu": "te",
            "bengali": "bn",
            "gujarati": "gu",
            "malayalam": "ml",
            "punjabi": "pa",
            "urdu": "ur"
        }
        lang = lang_map.get(lang_code.lower(), "en")
        
        # Handle transliterated text by using the correct language code
        # This addresses the issue where transliterated regional languages are detected as English
        if lang_code.lower() == "english" and is_likely_transliterated(text):
            # Try to detect if this might be transliterated Hindi or another language
            detected_lang = detect_transliterated_language(text)
            if detected_lang:
                lang = lang_map.get(detected_lang, lang)
                logger.info(f"Detected transliterated text in {detected_lang}, using language code: {lang}")

        tts = gTTS(text=text, lang=lang)
        filename = f"temp_{uuid.uuid4()}.mp3"
        tts.save(filename)
        
        logger.info(f"Generated audio file: {filename} for language: {lang}")
        
        # In Docker, we keep the file for serving via API
        if os.environ.get('KEEP_AUDIO_FILES') != 'true':
            # Set a cleanup flag to remove later if needed
            pass
            
        return filename

    except Exception as e:
        logger.error(f"[TTS Error]: {e}")
        return None

def is_likely_transliterated(text):
    """
    Basic heuristic to detect if text might be transliterated Indian language
    """
    # Common Hindi/Indian language transliterated patterns
    indicators = ['kya', 'hai', 'aap', 'main', 'mujhe', 'tumhe', 'humko', 'kitna', 
                 'kaise', 'kyun', 'kyon', 'nahin', 'nahi', 'haan', 'theek', 
                 'acha', 'accha', 'namaste', 'dhanyavad', 'shukriya']
    
    text_lower = text.lower()
    for word in indicators:
        if word in text_lower.split():
            return True
    return False

def detect_transliterated_language(text):
    """
    Attempt to detect which Indian language the transliterated text might be
    Currently focuses on Hindi as that's the most common case
    """
    # This is a simplified version - in production you'd want more sophisticated detection
    hindi_patterns = ['mujhe', 'tumhe', 'humko', 'aap', 'mai', 'hum', 'tum', 
                    'kya', 'kyun', 'kaise', 'kitna', 'kaun']
    
    text_lower = text.lower()
    hindi_matches = sum(1 for word in hindi_patterns if word in text_lower.split())
    
    if hindi_matches > 0:
        return "hindi"
    
    # Could expand with patterns for other languages
    return None
