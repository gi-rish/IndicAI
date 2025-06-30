#!/bin/bash
# Startup script for Indic AI Translation API

set -e

echo "Starting Indic AI Translation API initialization..."

# Check if MinIO is enabled
if [ "$USE_MINIO" = "true" ]; then
  echo "MinIO is enabled, checking connection..."
  
  # Wait for MinIO to be available
  MAX_RETRIES=30
  RETRY_INTERVAL=2
  
  for i in $(seq 1 $MAX_RETRIES); do
    echo "Attempting to connect to MinIO (attempt $i/$MAX_RETRIES)..."
    
    # Try to list buckets
    if python -c "
import os
from minio import Minio
try:
    client = Minio(
        '$MINIO_ENDPOINT:$MINIO_PORT',
        access_key='$MINIO_ACCESS_KEY',
        secret_key='$MINIO_SECRET_KEY',
        secure=True if '$MINIO_SECURE'.lower() == 'true' else False
    )
    buckets = client.list_buckets()
    print('Successfully connected to MinIO')
    
    # Check if our bucket exists, create if not
    bucket_name = os.getenv('MINIO_BUCKET', 'indic-ai-audio')
    found = False
    for bucket in buckets:
        if bucket.name == bucket_name:
            found = True
            break
    
    if not found:
        print(f'Creating bucket: {bucket_name}')
        client.make_bucket(bucket_name)
        print(f'Bucket {bucket_name} created successfully')
    else:
        print(f'Bucket {bucket_name} already exists')
    
    exit(0)
except Exception as e:
    print(f'Error connecting to MinIO: {e}')
    exit(1)
"; then
      echo "MinIO connection successful!"
      break
    else
      if [ $i -eq $MAX_RETRIES ]; then
        echo "Failed to connect to MinIO after $MAX_RETRIES attempts. Starting anyway..."
      else
        echo "MinIO not available yet, retrying in $RETRY_INTERVAL seconds..."
        sleep $RETRY_INTERVAL
      fi
    fi
  done
fi

# Run language detection initialization to fix issues with transliterated languages
echo "Initializing language detection model..."
python /app/init_language_detection.py

# Start the API server
echo "Starting Indic AI Translation API server..."
exec uvicorn translation_api:app --host 0.0.0.0 --port ${API_PORT:-8080} --reload
