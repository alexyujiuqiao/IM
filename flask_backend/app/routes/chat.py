import asyncio
import uuid
from pathlib import Path
import logging
import base64
from typing import Any

from flask import Blueprint, Response, request, current_app, jsonify
import os
from functools import wraps

# Shared parsing / response helpers
from ..utils.chat_utils import (
    parse_messages as _parse_messages,
    build_openai_response,
    audio_response_from_base64,
)

# ------------------------------------------------------------------
# Optional authentication toggle. Set DISABLE_AUTH=true (or 1/yes) in
# the environment, or start the server with the --no-auth flag (see
# run.py) to bypass JWT verification. In no-auth mode we expose the
# endpoints without requiring tokens and generate a stub identity.
# ------------------------------------------------------------------

_AUTH_DISABLED = os.getenv("DISABLE_AUTH", "false").lower() in ("1", "true", "yes")

if _AUTH_DISABLED:
    def jwt_required(*dargs, **dkwargs):  # type: ignore
        """No-op decorator used when auth is disabled."""
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    def get_jwt_identity():  # type: ignore
        """Return a dummy identity when auth is disabled."""
        return request.headers.get("X-User-Id", "anonymous")
else:
    from flask_jwt_extended import jwt_required, get_jwt_identity

from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)

bp = Blueprint("chat", __name__, url_prefix="/api/chat")

# ------------------------------------------------------------------
# Utility – parse OpenAI-style messages array produced by the Gradio
# front-end.  Returns (last_user_msg, history, input_type, image_content,
# audio_content).
# ------------------------------------------------------------------


def event_stream():
    # Simple demo stream
    for i in range(1, 6):
        yield f"data: chunk {i}\n\n"
        asyncio.sleep(1)


@bp.post("/v1/text")
@jwt_required()
def text_chat():
    data = request.get_json() or {}
    user_id = get_jwt_identity()
    
    messages = data.get("messages", [])
    model = data.get("model", "im-chat")
    logger.info(f"Chat request received from user: {user_id} - {len(messages)} messages")

    last_user_message, history, input_type, image_content, _audio_unused = _parse_messages(messages)

    if not last_user_message:
        return jsonify({"error": "No user message found"}), 400
    
    # Optimized approach: Direct TGI call with optional background RAG processing
    logger.info("Starting optimized chat pipeline...")
    try:
        # Use QwenChatService directly for fast response (like TGI playground)
        from ..services.qwen_chat_service import QwenChatService
        qwen_service = QwenChatService()
        
        # Build conversation messages for direct TGI call
        conversation_messages = []
        if history:
            conversation_messages.extend(history)
        if input_type == "image" and image_content:
            conversation_messages.append({"role": "user", "content": image_content})
        else:
            conversation_messages.append({"role": "user", "content": last_user_message})
        
        # Send full conversation to get immediate response
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            reply = loop.run_until_complete(qwen_service.send_chat(
                user_id, conversation_messages, type=input_type
            ))
        finally:
            loop.close()
        
        logger.info(f"Fast response generated for user: {user_id}")
        
        # Background RAG processing (non-blocking) for context storage
        try:
            rag_service = RAGService()
            # Run RAG processing in background without blocking response
            import threading
            def background_rag():
                try:
                    rag_service.rag_pipeline(user_id, last_user_message, conversation_messages, input_type, image_content)
                    logger.info(f"Background RAG processing completed for user: {user_id}")
                except Exception as e:
                    logger.warning(f"Background RAG processing failed: {e}")
            
            threading.Thread(target=background_rag, daemon=True).start()
        except Exception as e:
            logger.warning(f"RAG service not available: {e}")
        
        # Format response in OpenAI format
        response_data = build_openai_response(reply, messages, model)
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in RAG pipeline: {e}")
        logger.error(f"Error details: {type(e).__name__}: {str(e)}")
        # Fallback to direct Qwen service
        logger.info("Falling back to direct Qwen service...")
        from ..services.qwen_chat_service import QwenChatService
        qwen_service = QwenChatService()
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Build content list for the service
        content_list = []
        if history:
            for msg in history:
                content_list.append(msg)
        if input_type == "image" and image_content:
            content_list.append({"role": "user", "content": image_content})
        else:
            content_list.append({"role": "user", "content": last_user_message})
        
        reply = loop.run_until_complete(qwen_service.send_chat(
            user_id, content_list, type=input_type
        ))
        loop.close()
        
        # Format response in OpenAI format
        response_data = build_openai_response(reply, messages, model)
        return jsonify(response_data)


@bp.post("/v1/audio")
@jwt_required()
def audio_chat():
    """Handle audio input and return audio response using OpenAI-compatible format"""
    data = request.get_json() or {}
    user_id = get_jwt_identity()
    
    # Parse OpenAI format request
    messages = data.get("messages", [])
    model = data.get("model", "my-custom-model")
    max_tokens = data.get("max_tokens", 150)
    temperature = data.get("temperature", 0.7)
    
    logger.info(f"Audio chat request received from user: {user_id}")
    logger.info(f"Model: {model}")
    logger.info(f"Messages count: {len(messages)}")
    
    try:
        # Extract the last user message and build history
        last_user_message = None
        history = []
        transcription = ""
        
        for msg in messages:
            role = msg.get("role")
            msg_content = msg.get("content")
            
            if role == "user":
                # Handle multimodal content (text + audio)
                if isinstance(msg_content, list):
                    for item in msg_content:
                        if item.get("type") == "text":
                            last_user_message = item.get("text", "")
                        elif item.get("type") == "audio_url":
                            # Extract audio data from OpenAI format
                            audio_url = item.get("audio_url", {}).get("url", "")
                            if audio_url.startswith("data:audio/"):
                                # Extract base64 data from data URL
                                import base64
                                try:
                                    # Remove data URL prefix and decode
                                    audio_base64 = audio_url.split(",", 1)[1]
                                    from ..services.audio_service import AudioService
                                    audio_service = AudioService()
                                    result = audio_service.process_audio(audio_base64)
                                    transcription = result.get("transcription") or "[Unrecognized speech]"
                                    logger.info(f"Audio transcribed: {transcription}")
                                    # Use transcription as the message if no text provided
                                    if not last_user_message:
                                        last_user_message = transcription
                                except Exception as e:
                                    logger.error(f"Audio transcription failed: {e}")
                                    transcription = "[Audio transcription failed]"
                                    if not last_user_message:
                                        last_user_message = transcription
                else:
                    # Simple text content
                    last_user_message = msg_content
            elif role == "assistant":
                history.append({"role": "assistant", "content": msg_content})
        
        if not last_user_message:
            return jsonify({"error": "No user message found"}), 400
        
        # Use RAGService to handle conversation storage, user profile storage, and retrieval
        logger.info("Starting RAG pipeline for audio...")
        try:
            rag_service = RAGService()
            logger.info("RAGService initialized successfully for audio")
            
            # For audio input, we need to pass the audio content to RAG service
            # Find the audio content from the messages
            audio_content = None
            for msg in messages:
                if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                    for item in msg.get("content", []):
                        if item.get("type") == "audio_url":
                            audio_url = item.get("audio_url", {}).get("url", "")
                            if audio_url.startswith("data:audio/"):
                                # Extract base64 data from data URL
                                audio_base64 = audio_url.split(",", 1)[1]
                                audio_content = {
                                    "type": "audio_base64",
                                    "data": audio_base64
                                }
                                break
            
            # Use the audio content for RAG processing
            reply, voice_profile_name = rag_service.rag_pipeline(user_id, last_user_message, history, "audio", audio_content)
            logger.info(f"RAG pipeline completed for audio. Got text response: {reply[:50]}...")
            
            # DEBUG: Show full text response before TTS
            logger.info(f"DEBUG - Full text response before TTS: '{reply}'")
            logger.info(f"DEBUG - Text response length: {len(reply)} characters")
            logger.info(f"DEBUG - Text response type: {type(reply)}")
            
            # Convert text response to audio using TTS
            from ..services.tts_service import TTSService
            tts_service = TTSService()
            
            # DEBUG: Check TTS service status
            logger.info(f"DEBUG - TTS service available: {tts_service.is_available()}")
            
            if tts_service.is_available():
                logger.info("Converting RAG response to audio...")
                logger.info(f"DEBUG - About to call TTS with text: '{reply[:100]}...'")
                logger.info(f"DEBUG - TTS parameters: voice=alloy, model=tts-1, format=mp3")
                
                # Map voice_profile_name to OpenAI TTS voice code
                voice_map = {
                    "魅力女友": "nova",
                    "柔美女友": "shimmer",
                    "傲娇霸总": "onyx",
                    "正直青年": "echo"
                }
                tts_voice = voice_map.get(voice_profile_name, "alloy")

                audio_base64 = tts_service.text_to_speech_base64(
                    text=reply,
                    voice=tts_voice,
                    model="tts-1",
                    audio_format="mp3"
                )
                
                logger.info(f"DEBUG - TTS returned: {type(audio_base64)}")
                if audio_base64:
                    logger.info(f"DEBUG - TTS audio length: {len(audio_base64)} characters")
                    logger.info(f"DEBUG - TTS audio preview: {audio_base64[:50]}...")
                else:
                    logger.info(f"DEBUG - TTS returned None or empty")
                
                if audio_base64:
                    logger.info(f"Successfully converted RAG response to audio: {len(audio_base64)} characters")
                    # Decode base64 to binary audio data
                    audio_data = base64.b64decode(audio_base64)
                    
                    # Return audio response with transcription info
                    # Clean transcription for headers (remove newlines and limit length)
                    clean_transcription = transcription[:200].replace('\n', ' ').replace('\r', ' ')
                    headers = {
                        "Content-Type": "audio/mpeg",
                        "Content-Disposition": "attachment; filename=response.mp3",
                        "X-Transcription": clean_transcription
                    }
                    
                    return Response(audio_data, headers=headers)
                else:
                    logger.warning("TTS conversion failed, returning text response")
                    # Format response in OpenAI format
                    import time
                    response_data = {
                        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": reply
                                },
                                "finish_reason": "stop"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": len(str(messages)) // 4,
                            "completion_tokens": len(reply) // 4,
                            "total_tokens": (len(str(messages)) + len(reply)) // 4
                        }
                    }
                    return jsonify(response_data)
            else:
                logger.warning("TTS service not available, returning text response")
                # Format response in OpenAI format
                import time
                response_data = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": reply
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": len(str(messages)) // 4,
                        "completion_tokens": len(reply) // 4,
                        "total_tokens": (len(str(messages)) + len(reply)) // 4
                    }
                }
                return jsonify(response_data)
                
        except Exception as rag_error:
            logger.error(f"Error in RAG pipeline for audio: {rag_error}")
            logger.error(f"RAG error details: {type(rag_error).__name__}: {str(rag_error)}")
            
            # Fallback to direct Qwen service
            logger.info("Falling back to direct Qwen service for audio...")
            logger.info(f"DEBUG - Fallback: transcription='{transcription}'")
            
            from ..services.qwen_chat_service import QwenChatService
            qwen_service = QwenChatService()
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Build content list for the service
            content_list = []
            if history:
                for msg in history:
                    content_list.append(msg)
            content_list.append({"role": "user", "content": last_user_message})
            
            reply = loop.run_until_complete(qwen_service.send_chat(
                user_id, content_list, type="text"
            ))
            loop.close()
            
            # Format response in OpenAI format
            import time
            response_data = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": reply
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": len(str(messages)) // 4,
                    "completion_tokens": len(reply) // 4,
                    "total_tokens": (len(str(messages)) + len(reply)) // 4
                }
            }
            return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in audio chat: {e}")
        logger.error(f"Error details: {type(e).__name__}: {str(e)}")
        
        # Fallback: return error message
        return {"error": "Audio processing failed"}, 500


# ------------------------------------------------------------------
# Mobile unified endpoint – single entry point for iOS / Android clients
# ------------------------------------------------------------------


@bp.post("/v1/mobile")
@jwt_required()
def mobile_chat():
    """Unified text / image / audio endpoint for mobile apps (OpenAI schema)."""
    data = request.get_json() or {}
    user_id = get_jwt_identity()

    messages = data.get("messages", [])
    model = data.get("model", "im-chat")

    # ------------------------------------------------------------
    # Parse messages array
    # ------------------------------------------------------------
    last_user_message, history, input_type, image_content, audio_content = _parse_messages(messages)

    if not last_user_message and input_type == "text":
        return jsonify({"error": "No user message found"}), 400

    rag_service = RAGService()

    # ------------------------------------------------------------
    # Run RAG pipeline depending on modality
    # ------------------------------------------------------------
    if input_type == "audio":
        reply, voice_profile = rag_service.rag_pipeline(
            user_id,
            last_user_message or "[audio]",
            history,
            "audio",
            audio_content,
        )

        # Attempt to synthesise audio answer too (so mobile can play it)
        from ..services.tts_service import TTSService
        tts = TTSService()
        audio_b64 = None
        if tts.is_available():
            voice_map = {
                "魅力女友": "nova",
                "柔美女友": "shimmer",
                "傲娇霸总": "onyx",
                "正直青年": "echo",
            }
            tts_voice = voice_map.get(voice_profile, "alloy")
            audio_b64 = tts.text_to_speech_base64(reply, tts_voice, model="tts-1", audio_format="mp3")

        if audio_b64:
            assistant_content: Any = [
                {"type": "text", "text": reply},
                {"type": "audio_url", "audio_url": {"url": f"data:audio/mpeg;base64,{audio_b64}"}},
            ]
        else:
            assistant_content = reply

    elif input_type == "image":
        reply, _ = rag_service.rag_pipeline(
            user_id,
            last_user_message or "[image]",
            history,
            "image",
            image_content,
        )
        assistant_content = reply
    else:
        # plain text
        reply, _ = rag_service.rag_pipeline(user_id, last_user_message, history, "text")
        assistant_content = reply

    # ------------------------------------------------------------
    # Build OpenAI-style response
    # ------------------------------------------------------------
    resp_data = build_openai_response(reply="" if isinstance(assistant_content, list) else assistant_content, messages=messages, model=model)

    # If assistant_content is a list (audio case) overwrite message content
    if isinstance(assistant_content, list):
        resp_data["choices"][0]["message"]["content"] = assistant_content

    return jsonify(resp_data)


# ------------------------------------------------------------------
# Memory Management Endpoints
# ------------------------------------------------------------------

@bp.get("/memory/profile/<user_id>")
@jwt_required()
def get_user_profile(user_id):
    """Get user profile from memory service."""
    try:
        from ..services.memory_service import MemoryService
        memory_service = MemoryService()
        profile = memory_service.get_user_profile(user_id)
        return jsonify({"profile": profile})
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({"error": "Failed to get user profile"}), 500


@bp.post("/memory/profile/<user_id>")
@jwt_required()
def update_user_profile(user_id):
    """Update user profile in memory service."""
    try:
        data = request.get_json() or {}
        from ..services.memory_service import MemoryService
        memory_service = MemoryService()
        
        # Process the profile update through memory service
        # This will trigger profile extraction and update
        messages = [{"role": "user", "content": f"Update my profile: {data}"}]
        memory_service.process_conversation(user_id, messages)
        
        # Get updated profile
        profile = memory_service.get_user_profile(user_id)
        return jsonify({"profile": profile, "message": "Profile updated successfully"})
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return jsonify({"error": "Failed to update user profile"}), 500


@bp.get("/memory/summary/<user_id>")
@jwt_required()
def get_memory_summary(user_id):
    """Get conversation memory summary for user."""
    try:
        from ..services.memory_service import MemoryService
        memory_service = MemoryService()
        summary = memory_service.get_user_memory_summary(user_id)
        return jsonify({"summary": summary})
    except Exception as e:
        logger.error(f"Error getting memory summary: {e}")
        return jsonify({"error": "Failed to get memory summary"}), 500


@bp.delete("/memory/<user_id>")
@jwt_required()
def clear_user_memory(user_id):
    """Clear all memory for a user."""
    try:
        from ..services.memory_service import MemoryService
        memory_service = MemoryService()
        memory_service.clear_user_memory(user_id)
        return jsonify({"message": "Memory cleared successfully"})
    except Exception as e:
        logger.error(f"Error clearing user memory: {e}")
        return jsonify({"error": "Failed to clear memory"}), 500
