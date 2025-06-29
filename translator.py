from deep_translator import GoogleTranslator
import sys
import os
from pathlib import Path

# Add the utils directory to the path to import gemini_client
sys.path.append(str(Path(__file__).parent))
try:
    from utils.gemini_client import get_gemini_response
except ImportError:
    print("Warning: gemini_client module not found. Using only deep-translator.")
    get_gemini_response = None

def translate_to_english(text, source_lang_code):
    """
    Translate text from source language to English using Gemini first, 
    falling back to deep-translator if Gemini fails.
    
    Args:
        text (str): Text to translate
        source_lang_code (str): Source language code (e.g., 'hi', 'ta', 'te')
        
    Returns:
        str: Translated text in English
    """
    if source_lang_code == "en":
        return text
    
    # Try Gemini first if available
    if get_gemini_response:
        try:
            # Map language codes to full names for better Gemini understanding
            language_name = {
                "hi": "Hindi",
                "kn": "Kannada",
                "ta": "Tamil",
                "mr": "Marathi",
                "en": "English"
            }.get(source_lang_code, source_lang_code)
            
            # More detailed prompt for Gemini
            prompt = f"""Translate the following text from {language_name} to English.
            The text may be written in Latin script (transliterated {language_name}).
            Only return the translated English text, nothing else:
            
            {text}"""
            
            translated = get_gemini_response(prompt)
            
            # Check if Gemini returned an error message or mentioned language codes
            if ("Sorry, I couldn't translate" in translated or 
                "I couldn't translate" in translated.lower() or
                "language code" in translated.lower() or
                "don't know what language" in translated.lower()):
                raise Exception("Gemini translation failed or returned error message")
                
            return translated
        except Exception as e:
            print(f"⚠️ GEMINI FAILED: {e}")
            print(f"🔄 FALLING BACK TO GOOGLE TRANSLATOR for {source_lang_code} → English translation")
            # Fall back to deep-translator
    
    # Use deep-translator as fallback
    try:
        translated = GoogleTranslator(source=source_lang_code, target="en").translate(text)
        return translated
    except Exception as e:
        print(f"Translation to English failed with both methods: {e}")
        return text

def translate_back(text, target_lang_code):
    """
    Translate text from English back to target language using Gemini first,
    falling back to deep-translator if Gemini fails.
    
    Args:
        text (str): Text in English to translate
        target_lang_code (str): Target language code (e.g., 'hi', 'ta', 'te')
        
    Returns:
        str: Translated text in target language
    """
    if target_lang_code == "en":
        return text
    
    # Debug the target language code
    print(f"[DEBUG] Translating back to language code: '{target_lang_code}'")
    
    # Ensure we have the correct language code for translation
    # ISO language codes for reference:
    # Hindi: hi, Kannada: kn, Tamil: ta, Marathi: mr
    
    # Try Gemini first if available
    if get_gemini_response:
        try:
            # Be explicit about the language name for Gemini
            language_name = {
                "hi": "Hindi",
                "kn": "Kannada",
                "ta": "Tamil",
                "mr": "Marathi",
                "en": "English"
            }.get(target_lang_code, target_lang_code)
            
            # More detailed prompt for Gemini with script information
            script_info = {
                "hi": "Devanagari",
                "kn": "Kannada",
                "ta": "Tamil",
                "mr": "Devanagari",
                "en": "Latin"
            }.get(target_lang_code, "")
            
            prompt = f"""Translate the following English text to {language_name}.
            Use the proper {script_info} script for {language_name}.
            Make sure the translation is complete and accurate.
            Only return the translated text, nothing else:
            
            {text}"""
            
            print(f"[DEBUG] Gemini prompt: {prompt}")
            
            translated = get_gemini_response(prompt)
            print(f"[DEBUG] Gemini response: {translated[:100]}...")
            
            # More comprehensive error checking
            if ("Sorry, I couldn't translate" in translated or 
                "I couldn't translate" in translated.lower() or
                "language code" in translated.lower() or
                "don't know what language" in translated.lower() or
                len(translated.strip()) < 5):  # Very short responses are likely errors
                raise Exception("Gemini translation failed or returned error message")
                
            return translated
        except Exception as e:
            print(f"⚠️ GEMINI FAILED: {e}")
            print(f"🔄 FALLING BACK TO GOOGLE TRANSLATOR for English → {language_name} translation")
            # Fall back to deep-translator
    
    # Use deep-translator as fallback
    try:
        print(f"[DEBUG] Using deep-translator with source='en', target='{target_lang_code}'")
        translated = GoogleTranslator(source="en", target=target_lang_code).translate(text)
        print(f"[DEBUG] Deep-translator result: {translated[:100]}...")
        return translated
    except Exception as e:
        print(f"Translation back to {target_lang_code} failed with both methods: {e}")
        return text
