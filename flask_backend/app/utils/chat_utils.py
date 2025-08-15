from __future__ import annotations

import base64
import time
import uuid
import logging
from typing import Any, List, Tuple, Dict, Optional

from flask import Response

logger = logging.getLogger(__name__)

__all__ = [
    "parse_messages",
    "build_openai_response",
    "audio_response_from_base64",
]


def parse_messages(messages: List[Dict[str, Any]]) -> Tuple[str | None, List[Dict[str, str]], str, Optional[Dict], Optional[Dict]]:
    """Parse the OpenAI messages list sent by the front-end.

    Returns:
        last_user_message   - str | None
        history             - list of {role, content} *assistant* messages
        input_type          - "text" | "image" | "audio"
        image_content       - dict with keys {type, data} if present
        audio_content       - dict with keys {type, data} if present
    """
    last_user_message: str | None = None
    history: List[Dict[str, str]] = []
    input_type = "text"
    image_content: Optional[Dict] = None
    audio_content: Optional[Dict] = None

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")

        if role == "assistant":
            history.append({"role": "assistant", "content": content})
            continue

        if role != "user":
            # ignore system / tool messages for now
            continue

        # ----- user message parsing -----
        if isinstance(content, list):
            for part in content:
                ptype = part.get("type")
                if ptype == "text":
                    last_user_message = part.get("text", "")
                elif ptype == "image_url":
                    url = part.get("image_url", {}).get("url", "")
                    if url.startswith("data:image"):
                        # Handle base64 images
                        image_content = {
                            "type": "image_base64",
                            "data": url.split(",", 1)[1] if "," in url else url,
                        }
                        input_type = "image"
                    elif url.startswith("https://") and ("s3.amazonaws.com" in url or "amazonaws.com" in url):
                        # Handle S3 URLs
                        image_content = {
                            "type": "image_url",
                            "data": url,
                        }
                        input_type = "image"
                elif ptype == "audio_url":
                    url = part.get("audio_url", {}).get("url", "")
                    if url.startswith("data:audio"):
                        # Handle base64 audio
                        audio_content = {
                            "type": "audio_base64",
                            "data": url.split(",", 1)[1] if "," in url else url,
                        }
                        input_type = "audio"
                    elif url.startswith("https://") and ("s3.amazonaws.com" in url or "amazonaws.com" in url):
                        # Handle S3 audio URLs
                        audio_content = {
                            "type": "audio_url",
                            "data": url,
                        }
                        input_type = "audio"
        else:
            # content is str or sth else
            last_user_message = content if isinstance(content, str) else str(content)

    return last_user_message, history, input_type, image_content, audio_content


def build_openai_response(reply: str, messages: List[Any], model: str) -> Dict[str, Any]:
    """Return a dict that mimics OpenAI chat completion response."""
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": reply},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(str(messages)) // 4,
            "completion_tokens": len(reply) // 4,
            "total_tokens": (len(str(messages)) + len(reply)) // 4,
        },
    }


def audio_response_from_base64(audio_b64: str, transcription: str = "") -> Response:
    """Convert base64 MP3 into Flask Response with proper headers."""
    audio_data = base64.b64decode(audio_b64)
    clean_trans = transcription[:200].replace("\n", " ").replace("\r", " ")
    headers = {
        "Content-Type": "audio/mpeg",
        "Content-Disposition": "attachment; filename=response.mp3",
        "X-Transcription": clean_trans,
    }
    return Response(audio_data, headers=headers) 