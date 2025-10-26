"""
Voice Transcription Client - Handles audio transcription to text.
Uses multiple fallback providers for robust transcription.
"""

import os
import logging
import requests
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_BASE_URL = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe an audio file to text using available transcription services.
    Tries multiple providers in order: Deepgram, OpenAI Whisper, then fallback.

    Args:
        audio_path: Path to the audio file (WAV, MP3, etc.)

    Returns:
        Transcribed text string

    Raises:
        ValueError: If no transcription service is available
        FileNotFoundError: If audio file doesn't exist
    """
    logger.info(f"Transcribing audio file: {audio_path}")

    # Check if audio file exists
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Try Deepgram first (fast and accurate)
    if DEEPGRAM_API_KEY:
        try:
            return transcribe_with_deepgram(audio_path)
        except Exception as e:
            logger.warning(f"Deepgram transcription failed: {e}, trying next provider...")

    # Try OpenAI Whisper next
    if OPENAI_API_KEY:
        try:
            return transcribe_with_openai(audio_path)
        except Exception as e:
            logger.warning(f"OpenAI transcription failed: {e}, trying next provider...")

    # Try speech_recognition library as fallback (uses Google)
    try:
        result = transcribe_audio_fallback(audio_path)
        if result:
            return result
    except Exception as e:
        logger.warning(f"Fallback transcription failed: {e}")

    # If all methods fail
    raise ValueError(
        "No transcription service available. Please set OPENAI_API_KEY or DEEPGRAM_API_KEY, "
        "or install speech_recognition library for fallback transcription."
    )


def transcribe_with_deepgram(audio_path: str) -> str:
    """
    Transcribe audio using Deepgram API.

    Args:
        audio_path: Path to audio file

    Returns:
        Transcribed text
    """
    logger.info("Using Deepgram for transcription")

    url = "https://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/*"
    }

    params = {
        "model": "nova-2",
        "smart_format": "true",
        "punctuate": "true"
    }

    with open(audio_path, "rb") as audio_file:
        response = requests.post(
            url,
            headers=headers,
            params=params,
            data=audio_file,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]

        logger.info(f"Deepgram transcription successful: {transcript}")
        return transcript


def transcribe_with_openai(audio_path: str) -> str:
    """
    Transcribe audio using OpenAI Whisper API.

    Args:
        audio_path: Path to audio file

    Returns:
        Transcribed text
    """
    logger.info("Using OpenAI Whisper for transcription")

    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    with open(audio_path, "rb") as audio_file:
        files = {
            "file": audio_file,
            "model": (None, "whisper-1")
        }

        response = requests.post(
            url,
            headers=headers,
            files=files,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        transcript = result["text"]

        logger.info(f"OpenAI transcription successful: {transcript}")
        return transcript


def transcribe_audio_fallback(audio_path: str) -> Optional[str]:
    """
    Fallback transcription method using speech_recognition library with Google.
    This is free but requires internet connection and the speech_recognition library.

    Args:
        audio_path: Path to the audio file

    Returns:
        Transcribed text or None if transcription fails
    """
    logger.info("Using fallback transcription method (Google Speech Recognition)")

    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        # Convert audio file to WAV if needed
        audio_file_path = audio_path
        if not audio_path.lower().endswith('.wav'):
            logger.info("Converting audio to WAV format for speech_recognition")
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(audio_path)
                import tempfile
                wav_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                audio.export(wav_file.name, format='wav')
                audio_file_path = wav_file.name
                logger.info(f"Converted to WAV: {audio_file_path}")
            except ImportError:
                logger.warning("pydub not installed, trying with original file format")
            except Exception as e:
                logger.warning(f"Audio conversion failed: {e}, trying with original file")

        with sr.AudioFile(audio_file_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            logger.info(f"Fallback transcription successful: {text}")
            return text

    except ImportError:
        logger.warning("speech_recognition library not installed. Install with: pip install SpeechRecognition")
        return None
    except Exception as e:
        logger.error(f"Fallback transcription failed: {e}")
        return None


def check_transcription_available() -> dict:
    """
    Check which transcription services are available.

    Returns:
        Dictionary with available services and their status
    """
    services = {
        "deepgram": bool(DEEPGRAM_API_KEY),
        "openai": bool(OPENAI_API_KEY),
        "google_fallback": False
    }

    # Check if speech_recognition is available
    try:
        import speech_recognition as sr
        services["google_fallback"] = True
    except ImportError:
        pass

    return services


if __name__ == "__main__":
    # Test the transcription client
    print("Voice Transcription Client")
    print("-" * 40)

    services = check_transcription_available()

    print("\nAvailable transcription services:")
    if services["deepgram"]:
        print("✓ Deepgram API (fastest, most accurate)")
    else:
        print("✗ Deepgram API - set DEEPGRAM_API_KEY to enable")

    if services["openai"]:
        print("✓ OpenAI Whisper (high quality)")
    else:
        print("✗ OpenAI Whisper - set OPENAI_API_KEY to enable")

    if services["google_fallback"]:
        print("✓ Google Speech Recognition (free fallback)")
    else:
        print("✗ Google Speech Recognition - install SpeechRecognition to enable")

    if not any(services.values()):
        print("\n⚠️  WARNING: No transcription service available!")
        print("\nTo enable voice input, choose one:")
        print("1. Deepgram (recommended): Get key from https://deepgram.com")
        print("   Set DEEPGRAM_API_KEY in .env")
        print("2. OpenAI Whisper: Get key from https://platform.openai.com")
        print("   Set OPENAI_API_KEY in .env")
        print("3. Free fallback: Install SpeechRecognition")
        print("   pip install SpeechRecognition pydub")
    else:
        print("\n✓ Voice transcription is ready!")
