#!/usr/bin/env python3
"""
Test script for the Translation API
This script sends test requests to the Translation API to verify it's working correctly
"""

import requests
import json
import sys

# Try different ports
PORTS_TO_TRY = [8080, 8000, 8001, 8002, 8003, 8004, 8005]

# Find the correct port
def find_working_port():
    for port in PORTS_TO_TRY:
        try:
            url = f"http://localhost:{port}"
            print(f"Trying API at {url}...")
            response = requests.get(f"{url}/health", timeout=1)
            if response.status_code == 200:
                print(f"✅ Found API running on port {port}")
                return url
        except Exception:
            pass
    print("❌ Could not find API running on any port")
    return None

# API endpoint
API_URL = None

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Health check status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Error checking health: {e}")
        return False

def test_translation(text, expected_language=None):
    """Test the translation endpoint with the given text"""
    try:
        payload = {
            "text": text,
            "chat_history": []
        }
        
        print(f"\n--- Testing translation of: '{text}' ---")
        response = requests.post(f"{API_URL}/translate", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Detected language: {result['detected_language']}")
            print(f"English translation: {result['english_translation']}")
            print(f"Response in detected language: {result['translated_text']}")
            print(f"Is transliteration: {result['is_transliteration']}")
            
            if expected_language and result['detected_language'] != expected_language:
                print(f"⚠️ WARNING: Expected language '{expected_language}' but got '{result['detected_language']}'")
            
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error testing translation: {e}")
        return False

def main():
    """Run all tests"""
    global API_URL
    
    # Find the working port
    API_URL = find_working_port()
    if not API_URL:
        print("Could not find API server, exiting")
        sys.exit(1)
    
    if not test_health():
        print("Health check failed, exiting")
        sys.exit(1)
    
    # Test English
    test_translation("How much loan can I get?", "english")
    
    # Test Hindi transliteration - previously misdetected as Tamil
    test_translation("mujhe kitna loan amount milega?", "hindi")
    
    # Test Kannada transliteration - previously misdetected as English
    test_translation("nange onbaord madbeku", "kannada")
    
    # Test Tamil transliteration
    test_translation("enakku loan vaanganum", "tamil")
    
    # Test Marathi transliteration
    test_translation("mala loan pahije", "marathi")

if __name__ == "__main__":
    main()
