import base64
from typing import Dict, Any

class MediaProcessingService:
    @staticmethod
    def file_to_base64(file_path: str) -> str:
        """Encode a file to base64 string."""
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    @staticmethod
    def format_image_message(base64_str: str, prompt: str = "What is this?") -> Dict[str, Any]:
        """Format an image message for OpenAI-compatible API."""
        image_message = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_str}"
            }
        }
        return [image_message, {"type": "text", "text": prompt}]

    @staticmethod
    def format_audio_message(base64_str: str, prompt: str = "Please transcribe or analyze this audio.") -> Dict[str, Any]:
        """Format an audio message for OpenAI-compatible API."""
        audio_message = {
            "type": "audio_url",
            "audio_url": {
                "url": f"data:audio/wav;base64,{base64_str}"
            }
        }
        return [audio_message, {"type": "text", "text": prompt}] 