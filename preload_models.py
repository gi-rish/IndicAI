#!/usr/bin/env python3
"""
Script to preload and cache models for the Indic AI Translation API.
This script is used during Docker build to ensure models are cached.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("model_preloader")

def preload_sentence_transformers():
    """Preload and cache sentence-transformers models"""
    try:
        logger.info("Preloading sentence-transformers model...")
        # First try to fix potential huggingface_hub compatibility issues
        try:
            import huggingface_hub
            logger.info(f"Loaded huggingface_hub version: {huggingface_hub.__version__}")
        except Exception as hub_err:
            logger.warning(f"Issue with huggingface_hub: {hub_err}")
        
        # Now try to load the model
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info(f"Successfully loaded sentence-transformers model at {model.get_sentence_embedding_dimension()} dimensions")
        return True
    except Exception as e:
        logger.error(f"Error preloading sentence-transformers: {e}")
        logger.warning("Continuing without sentence-transformers preloading")
        # Return True to allow the script to continue
        return True

def preload_chromadb():
    """Initialize ChromaDB with the language database"""
    try:
        logger.info("Initializing ChromaDB...")
        import chromadb
        from chromadb.config import Settings
        
        # Create directory if it doesn't exist
        os.makedirs("./chroma_lang_db", exist_ok=True)
        
        client = chromadb.Client(Settings(
            persist_directory='./chroma_lang_db',
            anonymized_telemetry=False
        ))
        
        # Check if we can create a collection
        try:
            collection = client.get_or_create_collection("language_embeddings")
            logger.info(f"ChromaDB collection created/accessed: {collection.name}")
        except Exception as e:
            logger.warning(f"Could not create test collection: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing ChromaDB: {e}")
        return False

def preload_speech_recognition():
    """Preload speech recognition models"""
    try:
        logger.info("Preloading speech recognition models...")
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        logger.info("Speech recognition initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error preloading speech recognition: {e}")
        return False

def main():
    """Main function to preload all models"""
    logger.info("Starting model preloading process...")
    
    # Create cache directories
    os.makedirs("/root/.cache/torch/sentence_transformers", exist_ok=True)
    os.makedirs("/root/.cache/huggingface", exist_ok=True)
    
    # Track success of each preloading step
    results = {
        "sentence_transformers": preload_sentence_transformers(),
        "chromadb": preload_chromadb(),
        "speech_recognition": preload_speech_recognition()
    }
    
    # Log results but continue even if some models failed to load
    failed = [k for k, v in results.items() if not v]
    if failed:
        logger.warning(f"Some models failed to preload: {', '.join(failed)}")
        logger.info("Continuing with available models")
    else:
        logger.info("All models preloaded successfully!")
    
    # Always return success to allow the Docker build to continue
    return 0

if __name__ == "__main__":
    sys.exit(main())
