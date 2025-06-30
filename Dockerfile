FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    ffmpeg \
    libsndfile1 \
    tesseract-ocr \
    libtesseract-dev \
    git \
    python3-pyaudio \
    libasound-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements files
COPY requirements.txt requirements-db.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-db.txt

# Set environment variables for model caching
ENV TRANSFORMERS_CACHE=/app/.embeddings_cache
ENV SENTENCE_TRANSFORMERS_HOME=/app/.embeddings_cache
ENV HF_HOME=/app/.embeddings_cache

# Create cache directory
RUN mkdir -p /app/.embeddings_cache

# Copy application code
COPY . .

# Make the preload_with_retries.py script executable
RUN chmod +x /app/preload_with_retries.py

# Run the preloading script with retries
# This will handle both model preloading and language detection initialization
# with retry logic to handle Hugging Face rate limiting
RUN python /app/preload_with_retries.py

# Create a directory for MinIO data
RUN mkdir -p /app/minio_data

# Expose the port the app runs on
EXPOSE 8080

# Copy startup script
COPY startup.sh /app/
RUN chmod +x /app/startup.sh

# Command to run the application using the startup script
CMD ["/app/startup.sh"]
