# Indic AI Translation API

A FastAPI-based translation API that supports both text and voice input, with language detection for transliterated Indic languages, translation using Gemini API with fallback, GPT response generation, and audio synthesis.

## Features

- Text and voice input support
- Language detection for transliterated Indic languages
- Translation using Gemini API with fallback to deep-translator
- GPT response generation
- Audio synthesis and retrieval
- MinIO integration for audio storage

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# MinIO Configuration
USE_MINIO=true
MINIO_ENDPOINT=localhost
MINIO_PORT=9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=indic-ai-audio
MINIO_SECURE=false

# API Keys
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# API Configuration
API_PORT=8080
```

## Running with Docker

1. Make sure you have Docker and Docker Compose installed
2. Create a `.env` file with the required environment variables
3. Build and start the containers:

```bash
docker-compose up --build
```

The API will be available at http://localhost:8080 and MinIO console at http://localhost:9001

## API Endpoints

### Translation API

```
POST /translate
```

Request body:
```json
{
  "text": "Your text to translate",
  // OR
  "voiceKey": "voice-file-key-in-minio",
  "chat_history": []
}
```

Response:
```json
{
  "detected_language": "language_code",
  "translated_text": "translated_text_in_original_language",
  "audio_id": "audio_file_id",
  "english_translation": "english_translation",
  "english_response": "english_response",
  "is_transliteration": true|false
}
```

### Audio Retrieval

```
GET /audio/{audio_id}
```

Response:
```json
{
  "audio_url": "presigned_url_to_audio_file"
}
```

## Known Issues

- The system may incorrectly detect Hindi phrases like "mujhe kitna loan amount milega?" as Tamil
- When users type in regional languages using Latin script (transliteration), the system may sometimes detect them as English instead of the actual language
