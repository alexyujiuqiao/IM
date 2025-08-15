import os
import base64
from io import BytesIO
import logging
import openai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        """Initialize OpenAI TTS client"""
        try:
            # Initialize OpenAI client
            self.client = openai.OpenAI()
            logger.info("OpenAI TTS client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI TTS client: {e}")
            self.client = None
    
    def text_to_speech(self, text: str, voice: str = "alloy", 
                      model: str = "tts-1", audio_format: str = "mp3") -> bytes:
        """
        Convert text to speech using OpenAI TTS
        
        Args:
            text: The text to convert to speech
            voice: OpenAI TTS voice (alloy, echo, fable, onyx, nova, shimmer)
            model: TTS model (tts-1, tts-1-hd)
            audio_format: Audio format - mp3, opus, aac, flac (default: mp3)
        
        Returns:
            Audio data as bytes
        """
        if not self.client:
            logger.error("TTS client not initialized")
            return None
        
        try:
            # Call OpenAI TTS API
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=audio_format
            )
            
            # Get the audio content
            audio_content = response.content
            
            logger.info(f"Successfully converted text to speech: {len(text)} characters")
            return audio_content
            
        except Exception as e:
            logger.error(f"Error in text-to-speech conversion: {e}")
            return None
    
    def text_to_speech_base64(self, text: str, voice: str = "alloy", 
                             model: str = "tts-1", audio_format: str = "mp3") -> str:
        """
        Convert text to speech and return as base64 encoded string
        
        Args:
            text: The text to convert to speech
            voice: OpenAI TTS voice
            model: TTS model
            audio_format: Audio format
        
        Returns:
            Base64 encoded audio data
        """
        audio_data = self.text_to_speech(text, voice, model, audio_format)
        if audio_data:
            return base64.b64encode(audio_data).decode('utf-8')
        return None
    
    def get_available_voices(self) -> list:
        """
        Get available OpenAI TTS voices
        
        Returns:
            List of available voice information
        """
        voices = [
            {
                "name": "alloy",
                "description": "A balanced, neutral voice suitable for most content",
                "gender": "neutral"
            },
            {
                "name": "echo",
                "description": "A warm, friendly voice with a natural tone",
                "gender": "neutral"
            },
            {
                "name": "fable",
                "description": "A clear, professional voice with good articulation",
                "gender": "neutral"
            },
            {
                "name": "onyx",
                "description": "A deep, authoritative voice with gravitas",
                "gender": "male"
            },
            {
                "name": "nova",
                "description": "A bright, energetic voice with enthusiasm",
                "gender": "female"
            },
            {
                "name": "shimmer",
                "description": "A soft, gentle voice with warmth",
                "gender": "female"
            }
        ]
        
        logger.info(f"Retrieved {len(voices)} OpenAI TTS voices")
        return voices
    
    def is_available(self) -> bool:
        """Check if TTS service is available"""
        return self.client is not None 