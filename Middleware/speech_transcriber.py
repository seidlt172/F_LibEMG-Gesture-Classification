"""
speech_transcriber.py
=====================
Converts audio files (WAV) to text using OpenAI Whisper (local, offline).

Usage:
    transcriber = SpeechTranscriber()
    text = transcriber.transcribe("temp_voice.wav")
    # returns: "Das ist mein Text"
"""

import os
import logging
import whisper

logger = logging.getLogger(__name__)


class SpeechTranscriber:
    """Local Whisper-based speech-to-text converter."""
    
    def __init__(self, model_name="base"):
        """
        Initialize Whisper model.
        
        Args:
            model_name (str): Whisper model size
                - "tiny" (39M, fastest)
                - "base" (140M, balanced)  <- recommended
                - "small" (244M, better quality)
                - "medium" (769M, high quality)
                - "large" (2.9G, best quality)
        """
        logger.info(f"[SpeechTranscriber] Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name)
        logger.info(f"[SpeechTranscriber] Whisper model loaded successfully")
    
    def transcribe(self, audio_file_path):
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path (str): Path to WAV file
            
        Returns:
            str: Transcribed text (German will be auto-detected)
        """
        # Normalize path - remove .. and backslashes issues
        audio_file_path = os.path.normpath(os.path.abspath(audio_file_path))
        logger.info(f"[SpeechTranscriber] Transcribing: {audio_file_path}")
        
        # Verify file exists
        if not os.path.exists(audio_file_path):
            logger.error(f"[SpeechTranscriber] Audio file not found: {audio_file_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Check file size
        file_size = os.path.getsize(audio_file_path)
        logger.info(f"[SpeechTranscriber] File size: {file_size} bytes")
        if file_size < 100:
            logger.error(f"[SpeechTranscriber] ERROR: File too small ({file_size} bytes) - likely empty recording")
            raise ValueError(f"Audio file too small ({file_size} bytes) - empty recording?")
        
        try:
            result = self.model.transcribe(
                audio_file_path,
                language="de",  # German
                task="transcribe",
                fp16=False,  # Better CPU compatibility across platforms
            )
            
            text = result.get("text", "").strip()
            logger.info(f"[SpeechTranscriber] Transcription successful: {text}")
            return text
            
        except Exception as e:
            logger.error(f"[SpeechTranscriber] Transcription error: {e}", exc_info=True)
            return ""
