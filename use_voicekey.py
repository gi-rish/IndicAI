#!/usr/bin/env python3
"""
Script to test the translation API using an existing voiceKey
"""

import requests
import json
import sys
import time

# API endpoint - using local server
API_ENDPOINT = "http://localhost:8080/translate"

def test_with_voicekey(voicekey):
    """Test the translation API with an existing voiceKey"""
    print(f"\n{'='*50}")
    print(f"Testing with existing voiceKey: {voicekey}")
    
    # Prepare the payload with the voiceKey
    payload = {
        "voiceKey": voicekey,
        "chat_history": []
    }
    
    try:
        # Send the request to the API
        print(f"Sending request to {API_ENDPOINT} with voiceKey: {voicekey}")
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
                print("\nRequesting audio URL with wait parameter...")
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

def main():
    """Main function"""
    # Check if a voiceKey was provided as a command-line argument
    if len(sys.argv) > 1:
        voicekey = sys.argv[1]
    else:
        # Use the voiceKey from the previous test
        voicekey = "test_hi_trans_cf026915-0b47-4b78-897b-20ef98b569cf"
    
    # Test with the voiceKey
    test_with_voicekey(voicekey)
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
