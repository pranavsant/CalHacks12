"""
Vapi Client - Handles voice transcription using Vapi's Voice AI API.
This module provides functions to transcribe audio files to text.
"""

import os
import logging
import requests
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vapi API configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_BASE_URL = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe an audio file to text using Vapi's API.

    Args:
        audio_path: Path to the audio file (WAV, MP3, etc.)

    Returns:
        Transcribed text string

    Raises:
        ValueError: If VAPI_API_KEY is not set
        requests.RequestException: If the API call fails
    """
    logger.info(f"Transcribing audio file: {audio_path}")

    if not VAPI_API_KEY:
        logger.error("VAPI_API_KEY not found in environment variables")
        raise ValueError("VAPI_API_KEY environment variable is required for voice transcription")

    # Check if audio file exists
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        # NOTE: This is a placeholder implementation.
        # The actual Vapi API endpoints and request format may differ.
        # Refer to Vapi documentation at https://docs.vapi.ai for the correct implementation.

        # Example implementation (adjust based on actual Vapi API):
        # Option 1: Direct transcription endpoint
        # url = f"{VAPI_BASE_URL}/transcribe"
        #
        # with open(audio_path, 'rb') as audio_file:
        #     files = {'audio': audio_file}
        #     headers = {'Authorization': f'Bearer {VAPI_API_KEY}'}
        #
        #     response = requests.post(url, files=files, headers=headers, timeout=30)
        #     response.raise_for_status()
        #
        #     result = response.json()
        #     transcribed_text = result.get('text', '')
        #
        #     logger.info(f"Successfully transcribed: {transcribed_text}")
        #     return transcribed_text

        # Option 2: Using Vapi's assistant/call creation
        # Vapi is primarily designed for real-time voice calls
        # For file transcription, you might need to:
        # 1. Create a temporary assistant configured for transcription
        # 2. Create a call with the audio file
        # 3. Poll for the transcription result

        logger.warning("Vapi transcription not fully implemented - using placeholder")
        logger.warning("Please refer to https://docs.vapi.ai for actual implementation")

        # For development/testing purposes, return a placeholder
        # This allows the system to work with text-only input
        raise NotImplementedError(
            "Vapi audio transcription requires API integration. "
            "Please use text input or implement the Vapi API calls. "
            "See https://docs.vapi.ai for documentation."
        )

    except requests.RequestException as e:
        logger.error(f"Vapi API request failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in transcribe_audio: {e}")
        raise


def transcribe_audio_fallback(audio_path: str) -> Optional[str]:
    """
    Fallback transcription method using alternative services.
    This can use services like Google Speech Recognition, AssemblyAI, etc.

    Args:
        audio_path: Path to the audio file

    Returns:
        Transcribed text or None if transcription fails
    """
    logger.info("Using fallback transcription method")

    try:
        # Option: Use speech_recognition library as fallback
        # Uncomment if you want to add this as a backup:
        #
        # import speech_recognition as sr
        # recognizer = sr.Recognizer()
        #
        # with sr.AudioFile(audio_path) as source:
        #     audio = recognizer.record(source)
        #     text = recognizer.recognize_google(audio)
        #     logger.info(f"Fallback transcription successful: {text}")
        #     return text

        logger.warning("No fallback transcription method configured")
        return None

    except Exception as e:
        logger.error(f"Fallback transcription failed: {e}")
        return None


def check_vapi_connection() -> bool:
    """
    Check if Vapi API is accessible and credentials are valid.

    Returns:
        True if connection is successful, False otherwise
    """
    if not VAPI_API_KEY:
        logger.warning("VAPI_API_KEY not configured")
        return False

    try:
        # Placeholder: actual health check endpoint may differ
        # url = f"{VAPI_BASE_URL}/health"
        # headers = {'Authorization': f'Bearer {VAPI_API_KEY}'}
        # response = requests.get(url, headers=headers, timeout=5)
        # return response.status_code == 200

        logger.info("Vapi connection check skipped (not implemented)")
        return False

    except Exception as e:
        logger.error(f"Vapi connection check failed: {e}")
        return False


if __name__ == "__main__":
    # Test the Vapi client
    print("Vapi Client")
    print("-" * 40)

    if VAPI_API_KEY:
        print(f"API Key configured: {VAPI_API_KEY[:10]}...")
        print(f"Base URL: {VAPI_BASE_URL}")
    else:
        print("WARNING: VAPI_API_KEY not set")
        print("Audio transcription will not work")

    print("\nTo enable voice input:")
    print("1. Get a Vapi API key from https://vapi.ai")
    print("2. Set VAPI_API_KEY environment variable")
    print("3. Implement the transcribe_audio function based on Vapi docs")
