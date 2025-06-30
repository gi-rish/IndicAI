#!/usr/bin/env python
import time
import sys
import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model_preloader")

def run_with_retries(cmd, max_retries=5, delay=30):
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt+1}/{max_retries}: Running {cmd}")
            result = subprocess.run(cmd, shell=True, check=True)
            return True  # Success
        except subprocess.CalledProcessError as e:
            logger.error(f"Attempt {attempt+1} failed with error: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Waiting {delay} seconds before retry...")
                time.sleep(delay)
                # Increase delay for next attempt (exponential backoff)
                delay = min(delay * 2, 300)  # Cap at 5 minutes
            else:
                logger.error(f"All {max_retries} attempts failed")
                return False  # All attempts failed

logger.info("Starting model preloading process with retry logic...")

# Run preload_models.py with retries
success1 = run_with_retries("python /app/preload_models.py")
logger.info(f"Model preloading {'succeeded' if success1 else 'failed but continuing'}")

# Also run language detection initialization with retries
# This addresses the issues with Hindi phrases being detected as Tamil
# and transliterated regional languages being detected as English
success2 = run_with_retries("python /app/init_language_detection.py")
logger.info(f"Language detection initialization {'succeeded' if success2 else 'failed but continuing'}")

# Continue even if preloading fails
sys.exit(0)
