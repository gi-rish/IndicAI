#!/usr/bin/env python3
"""
Script to test the voicekey parameter in the translation API.
This uploads a sample audio file to MinIO and then calls the API with the voicekey.
"""

import os
import uuid
import requests
import json
import io
import tempfile
import subprocess
import time
from minio import Minio
from minio.error import S3Error
from gtts import gTTS

# MinIO configuration - using remote server
MINIO_ENDPOINT = "3.6.132.24"
MINIO_PORT = 9000
MINIO_ACCESS_KEY = "SWMSC2SQP1ICJ0I84N81"
MINIO_SECRET_KEY = "bXwJ+wFwjpb9qP1S85bVsuXceO4oJtNK7+rZCS15"
MINIO_BUCKET = "indic-ai-audio"
MINIO_SECURE = False

# API endpoint - using local server
API_ENDPOINT = "http://localhost:8000/translate"

def create_test_audio(text, lang="hi"):
    """Create a test audio file directly in WAV format compatible with speech_recognition"""
    print(f"Creating test audio for text: '{text}' in language: {lang}")
    
    import numpy as np
    import wave
    import tempfile
    import io
    from gtts import gTTS
    
    # Create a simple WAV file with the right format
    # This is a direct approach to create a PCM WAV file
    try:
        # First create an MP3 with gTTS
        mp3_buffer = io.BytesIO()
        tts = gTTS(text=text, lang=lang)
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)
        
        # Create a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_path = wav_file.name
        
        # Use ffmpeg to convert to PCM WAV (16-bit, 16kHz, mono)
        import subprocess
        subprocess.run(
            ["ffmpeg", "-y", "-f", "mp3", "-i", "pipe:0", 
             "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_path],
            input=mp3_buffer.read(),
            check=True, capture_output=True
        )
        
        # Read the WAV file
        with open(wav_path, 'rb') as f:
            audio_data = f.read()
        
        # Clean up
        os.unlink(wav_path)
        
        return audio_data
    except Exception as e:
        print(f"Error creating audio: {e}")
        raise

def upload_to_minio(audio_data, object_name):
    """Upload audio data to MinIO"""
    try:
        # Initialize MinIO client
        endpoint = f"{MINIO_ENDPOINT}:{MINIO_PORT}"
        print(f"Connecting to MinIO at {endpoint}")
        
        minio_client = Minio(
            endpoint,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        
        # Check if bucket exists
        if not minio_client.bucket_exists(MINIO_BUCKET):
            print(f"Bucket {MINIO_BUCKET} does not exist, creating...")
            minio_client.make_bucket(MINIO_BUCKET)
        
        # Upload audio data
        audio_stream = io.BytesIO(audio_data)
        audio_stream.seek(0)
        
        minio_client.put_object(
            MINIO_BUCKET,
            f"{object_name}.wav",
            audio_stream,
            length=len(audio_data),
            content_type="audio/wav"
        )
        
        print(f"Successfully uploaded audio to MinIO with key: {object_name}")
        return True
    except S3Error as e:
        print(f"Error uploading to MinIO: {e}")
        return False

def test_translate_api_with_voicekey(voice_key):
    """Test the translation API with a voiceKey"""
    # Prepare the payload with the voiceKey
    payload = {
        "voiceKey": voice_key,
        "chat_history": []
    }
    
    try:
        # Send the request to the API
        print(f"Sending request to {API_ENDPOINT} with voiceKey: {voice_key}")
        response = requests.post(API_ENDPOINT, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            print("\nAPI Response:")
            print(f"Detected Language: {result.get('detected_language', 'Unknown')}")
            print(f"Is Transliteration: {result.get('is_transliteration', False)}")
            print(f"English Translation: {result.get('english_translation', 'N/A')}")
            print(f"English Response: {result.get('english_response', 'N/A')}")
            print(f"Translated Response: {result.get('response', 'N/A')}")
            print(f"Audio ID: {result.get('audio_id', 'N/A')}")
            
            # Get the audio URL if an audio_id was returned
            audio_id = result.get('audio_id')
            if audio_id:
                print("Requesting audio URL with wait parameter...")
                # Use the wait parameter to wait for the audio to be ready
                audio_url_response = requests.get(f"http://localhost:8080/audio/{audio_id}?wait=true&max_retries=5")
                
                if audio_url_response.status_code == 200:
                    response_data = audio_url_response.json()
                    if response_data.get('status') == 'ready':
                        audio_url = response_data.get('audio_url')
                        print(f"Audio URL: {audio_url}")
                    else:
                        print(f"Audio status: {response_data.get('status')}")
                        print(f"Message: {response_data.get('message')}")
                        print(f"Retry after: {response_data.get('retry_after')} seconds")
                        
                        # If audio is still processing, wait and try again
                        if response_data.get('status') == 'processing':
                            retry_after = response_data.get('retry_after', 2)
                            print(f"Waiting {retry_after} seconds before retrying...")
                            time.sleep(retry_after)
                            
                            # Try one more time
                            print("Retrying audio URL request...")
                            audio_url_response = requests.get(f"http://localhost:8080/audio/{audio_id}?wait=true&max_retries=5")
                            if audio_url_response.status_code == 200:
                                response_data = audio_url_response.json()
                                if response_data.get('status') == 'ready':
                                    audio_url = response_data.get('audio_url')
                                    print(f"Audio URL: {audio_url}")
                else:
                    print(f"Error getting audio URL: {audio_url_response.status_code}")
                    print(f"Response: {audio_url_response.text}")
            
            return result
        else:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

def test_transliteration_issue():
    """Test the transliteration issue specifically mentioned in the memories"""
    # These are the problematic transliterated Hindi phrases that were incorrectly detected
    problematic_phrases = [
        "mujhe kitna loan amount milega?",  # How much loan amount will I get?
        "mujhe loan chahiye",               # I need a loan
        "kitne din mein loan milega",       # In how many days will I get a loan?
        "kya main loan le sakta hoon"       # Can I take a loan?
    ]
    
    # Test each problematic phrase
    for i, phrase in enumerate(problematic_phrases):
        print(f"\n{'='*50}")
        print(f"Testing problematic transliterated Hindi phrase {i+1}: '{phrase}'")
        
        # Test direct API call with text
        print("\nTesting with direct text input:")
        payload = {
            "text": phrase,
            "chat_history": []
        }
        
        try:
            response = requests.post(API_ENDPOINT, json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"Detected Language: {result.get('detected_language', 'Unknown')}")
                print(f"Is Transliteration: {result.get('is_transliteration', False)}")
                print(f"English Translation: {result.get('english_translation', 'N/A')}")
            else:
                print(f"Error: API returned status code {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error calling API: {e}")
        
        # Now test with voice input
        print("\nTesting with voice input:")
        # Create a unique object name for MinIO
        object_name = f"test_hi_trans_{i}_{uuid.uuid4()}"
        
        # Create audio file (use 'hi' as the language code for gTTS)
        audio_data = create_test_audio(phrase, "hi")
        
        # Upload to MinIO
        if upload_to_minio(audio_data, object_name):
            # Test the API
            test_translate_api_with_voicekey(object_name)
        else:
            print(f"Failed to upload audio for phrase {i+1}")
        
        print(f"{'='*50}")

def main():
    """Main function to test the voicekey feature"""
    # Test a transliterated Hindi phrase
    phrase = "tumhara nam kya hai"  # What is your name?
    
    print(f"\n{'='*50}")
    print(f"Testing transliterated Hindi phrase: '{phrase}'")
    
    # Create a unique object name for MinIO
    object_name = f"test_hi_trans_{uuid.uuid4()}"
    
    # Create audio file (use 'hi' as the language code for gTTS)
    try:
        print("Creating audio file...")
        audio_data = create_test_audio(phrase, "hi")
        print("Audio file created successfully")
        
        # Upload to MinIO
        print("Uploading to MinIO...")
        if upload_to_minio(audio_data, object_name):
            print("Upload successful, testing API with voicekey...")
            # Test the API
            test_translate_api_with_voicekey(object_name)
        else:
            print("Failed to upload audio")
    except Exception as e:
        print(f"Error during test: {e}")
    
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
