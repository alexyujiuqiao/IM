import os
import requests
import base64
import logging
from typing import List, Tuple, Optional, Union
import time

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Basic configuration
# ---------------------------------------------------------------------------
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:5050")
TEXT_API_URL = f"{BASE_URL}/api/chat/v1/text"
AUDIO_API_URL = f"{BASE_URL}/api/chat/v1/audio"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
REGISTER_URL = f"{BASE_URL}/api/auth/register"
MOBILE_API_URL = f"{BASE_URL}/api/chat/v1/mobile"  # mobile endpoint
UPLOAD_IMAGE_URL = f"{BASE_URL}/api/chat/upload/image"
UPLOAD_AUDIO_URL = f"{BASE_URL}/api/chat/upload/audio"
UPLOAD_FILE_URL = f"{BASE_URL}/api/chat/upload/file" 

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def file_to_base64(path: Optional[str]) -> Optional[str]:
    """Read file *path* as base-64 string."""
    if not path:
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# ---------------------------------------------------------------------------
# Chat client abstraction
# ---------------------------------------------------------------------------

class ChatClient:
    """Tiny wrapper around the REST API so callers do not deal with raw requests."""

    def __init__(self, token: str = "", use_mobile_endpoint: bool = False) -> None:
        self.token = token.strip()
        self.use_mobile_endpoint = use_mobile_endpoint  # Added mobile flag

    # ------------------------------------------------------------------
    # Authentication helpers
    # ------------------------------------------------------------------
    @staticmethod
    def register(username: str, password: str) -> dict:
        resp = requests.post(REGISTER_URL, json={"username": username, "password": password}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def login(self, username: str, password: str) -> str:
        resp = requests.post(LOGIN_URL, json={"username": username, "password": password}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Extract token from the nested structure: data.attributes.token
        token = data.get("data", {}).get("attributes", {}).get("token", "")
        if not token:
            raise RuntimeError("Login succeeded but no token returned")
        self.token = token
        return token

    # ------------------------------------------------------------------
    # File Upload Methods
    # ------------------------------------------------------------------
    def upload_image(self, image_file: str) -> str:
        """Upload image file to S3 via backend endpoint"""
        if not self.token:
            raise RuntimeError("Not authenticated. Call login() first.")
        
        with open(image_file, 'rb') as f:
            files = {'file': f}
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.post(UPLOAD_IMAGE_URL, files=files, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get("success") and data.get("data"):
                return data["data"]["s3_url"]
            else:
                raise RuntimeError(f"Upload failed: {data.get('message', 'Unknown error')}")

    def upload_audio(self, audio_file: str) -> str:
        """Upload audio file to S3 via backend endpoint"""
        if not self.token:
            raise RuntimeError("Not authenticated. Call login() first.")
        
        with open(audio_file, 'rb') as f:
            files = {'file': f}
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.post(UPLOAD_AUDIO_URL, files=files, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get("success") and data.get("data"):
                return data["data"]["s3_url"]
            else:
                raise RuntimeError(f"Upload failed: {data.get('message', 'Unknown error')}")

    def upload_file(self, file_path: str) -> dict:
        """Upload any file to S3 via backend endpoint (auto-detects type)"""
        if not self.token:
            raise RuntimeError("Not authenticated. Call login() first.")
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.post(UPLOAD_FILE_URL, files=files, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Chatting
    # ------------------------------------------------------------------
    def chat(
        self,
        user_message: str,
        history: List[Tuple[str, str]],
        image_file: Optional[str] = None,
        audio_file: Optional[str] = None,
    ) -> Tuple[Union[str, bytes], bool, Optional[str]]:
        """Send a chat request with optional image and/or audio attachment.

        Returns (reply, is_audio, transcription).
        """
        # Convert history (tuple list) into OpenAI messages
        messages = []
        for u, a in history or []:
            # Gradio may store rich content as tuples (file_path, mime_type). Flatten them.
            if u:
                user_content = self._flatten_content(u)
                messages.append({"role": "user", "content": user_content})
            if a:
                assistant_content = self._flatten_content(a)
                messages.append({"role": "assistant", "content": assistant_content})

                # Build one combined multimodal content list
        content_items = []
        if user_message:
            content_items.append({"type": "text", "text": user_message})
        if image_file:
            # Upload image to S3 via backend endpoint
            try:
                s3_url = self.upload_image(image_file)
                content_items.append({"type": "image_url", "image_url": {"url": s3_url}})
                print(f"Image uploaded via backend: {s3_url}")
            except Exception as e:
                # Fallback to base64 if upload fails
                logger.warning(f"Image upload failed, falling back to base64: {e}")
                img_b64 = file_to_base64(image_file)
                content_items.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
        if audio_file:
            # Upload audio to S3 via backend endpoint
            try:
                s3_url = self.upload_audio(audio_file)
                content_items.append({"type": "audio_url", "audio_url": {"url": s3_url}})
                print(f"Audio uploaded via backend: {s3_url}")
            except Exception as e:
                # Fallback to base64 if upload fails
                logger.warning(f"Audio upload failed, falling back to base64: {e}")
                aud_b64 = file_to_base64(audio_file)
                content_items.append({"type": "audio_url", "audio_url": {"url": f"data:audio/wav;base64,{aud_b64}"}})
        

        # If only text exists, send as plain string; otherwise send multimodal list
        if len(content_items) == 1 and content_items[0]["type"] == "text":
            user_content: Union[str, list] = user_message or ""
        else:
            user_content = content_items

        messages.append({"role": "user", "content": user_content})

        payload = {"messages": messages, "model": "im-chat"}

        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        # Unified endpoint selection
        if self.use_mobile_endpoint:
            api_url = MOBILE_API_URL
        else:
            has_media = bool(image_file) or bool(audio_file)
            api_url = f"{BASE_URL}/api/chat/v1/completions" if has_media else TEXT_API_URL

        resp = requests.post(api_url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()

        # ---------------- Response Handling ---------------------------
        if self.use_mobile_endpoint:
            # Mobile endpoint response handling
            data = resp.json()
            if "choices" in data and data["choices"]:
                choice = data["choices"][0]
                message_content = choice["message"]["content"]
                
                if isinstance(message_content, list):
                    text_content = ""
                    audio_base64 = None
                    
                    for item in message_content:
                        if item.get("type") == "text":
                            text_content = item.get("text", "")
                        elif item.get("type") == "audio_url":
                            audio_url = item.get("audio_url", {}).get("url", "")
                            if audio_url.startswith("data:audio/"):
                                audio_base64 = audio_url.split(",", 1)[1] if "," in audio_url else None
                    
                    if audio_base64:
                        audio_bytes = base64.b64decode(audio_base64)
                        return audio_bytes, True, text_content
                    else:
                        return text_content, False, None
                else:
                    return message_content, False, None
            else:
                reply_text = data.get("reply") or data.get("text_response") or "[No reply]"
                return reply_text, False, data.get("transcription")
        else:
            # Standard endpoint handling
            if audio_file and resp.headers.get("content-type", "").startswith("audio/"):
                transcription = resp.headers.get("X-Transcription")
                return resp.content, True, transcription

            # Fall-back: assume JSON (OpenAI-style)
            data = resp.json()
            if "choices" in data and data["choices"]:
                reply_text = data["choices"][0]["message"]["content"]
            else:
                reply_text = data.get("reply") or data.get("text_response") or "[No reply]"
            return reply_text, False, data.get("transcription")

    def _flatten_content(self, item):
        """Convert UI tuples like (filepath, 'image') into human-readable placeholders
        suitable for the backend JSON payload. Non-tuple items are returned as-is.
        """
        # Audio tuples have mime 'audio/mpeg', images use 'image'.
        if isinstance(item, tuple) and len(item) == 2:
            _path, mime = item
            if mime.startswith("image"):
                return "[Image sent]"
            if mime.startswith("audio"):
                return "[Audio response]"
        return item 