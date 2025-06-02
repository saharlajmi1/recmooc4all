from openai import OpenAI
import os
from typing import Optional

def test_tts_lemonfox(audio_file: str):
    """Transcribe an audio file using Lemonfox's Whisper-1 model."""
    try:
        # Verify file exists
        if not os.path.exists(audio_file):
            raise ValueError(f"Audio file not found: {audio_file}")

        client = OpenAI(
            api_key="lk9dr9uIhWjQ0lGzIcmBlwCvAYdujNyg",
            base_url="https://api.lemonfox.ai/v1/",
        )   

        # Use context manager to ensure file is closed
        with open(audio_file, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language="fr"
            )

        # Validate transcription
        if not hasattr(transcript, 'text') or not transcript.text.strip():
            raise ValueError("Transcription failed: empty or invalid text")

        return transcript

    except Exception as e:
        print(f"❌ Error in test_tts_lemon: {str(e)}")
        raise


def generate_tts(text: str, language: str, output_file: Optional[str] = None) -> None:
    """
    Generate text-to-speech audio using the Lemonfox API with the specified language
    """
    # Supported languages
    supported_languages = {'en', 'ja', 'zh', 'es', 'fr', 'hi', 'it', 'pt','br'}
    
    # Validate language
    if language.lower() not in supported_languages:
        raise ValueError(f"Unsupported language: {language}. Supported languages: {supported_languages}")

    # Set default output file if not provided
    if output_file is None:
        output_file = f"speech_{language.lower()}.mp3"

    # Initialize Lemonfox client
    client = OpenAI(
        api_key="lk9dr9uIhWjQ0lGzIcmBlwCvAYdujNyg",
        base_url="https://api.lemonfox.ai/v1",
    )

    # Map languages to voices (adjust as per Lemonfox API documentation)
    voice_map = {
        'en': 'sarah',  # Known voice for English
        'ja': 'sakura',  # Placeholder; replace with actual voice if known
        'zh': 'xiaobei',
        'es': 'dora',
        'fr': 'siwis',
        'hi': 'alpha',
        'it': 'sara',
        'pt-br': 'clara'
    }

    try:
        # Create the TTS request
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice_map.get(language.lower(), 'default'),
            response_format="mp3",
            input=text
        )

        # Save the response content to a file
        with open(output_file, "wb") as f:
            f.write(response.content)

        print(f"Audio saved to {output_file}")

    except Exception as e:
        print(f"Error generating TTS: {str(e)}")
        raise
