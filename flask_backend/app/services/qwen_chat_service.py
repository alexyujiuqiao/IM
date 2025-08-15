import asyncio
import json
import logging
from typing import List
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

import httpx
from flask import current_app
import base64
from pathlib import Path
# Local services
from .image_service import ImageService
from .audio_service import AudioService
from .tts_service import TTSService

logger = logging.getLogger(__name__)

# Use the Hugging Face TGI API URL
HF_ENDPOINT = "https://huot6se97jhlqaem.us-east-1.aws.endpoints.huggingface.cloud"

class QwenChatService:
    def __init__(self):
        self.base_url = HF_ENDPOINT
        self.api_key = current_app.config.get("QWEN_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_chat(self, user_id: str, content_list: List[dict], type: str = "text") -> str:
        if type == "text":
            # Convert content_list to OpenAI-compatible messages format
            messages = self._convert_to_messages(content_list)
            return await self._send_text_chat(messages)
        elif type in ("image", "image_base64", "image_url"):
            # We expect exactly one user-sent image in the list. If multiple are
            # present we analyse only the last one.
            for msg in content_list:
                if (
                    msg["role"] == "user"
                    and isinstance(msg.get("content"), dict)
                    and msg["content"].get("type") in ("image_base64", "image_url")
                ):
                    image_data = msg["content"]["data"]
                    image_type = msg["content"]["type"]
                    try:
                        image_service = ImageService()
                        
                        if image_type == "image_base64":
                            # Handle base64 image
                            analysis = image_service.analyze_image(image_data)
                        elif image_type == "image_url":
                            # Handle S3 URL - download and convert to base64
                            import requests
                            try:
                                response = requests.get(image_data, timeout=10)
                                response.raise_for_status()
                                image_bytes = response.content
                                base64_str = base64.b64encode(image_bytes).decode('utf-8')
                                analysis = image_service.analyze_image(base64_str)
                            except Exception as e:
                                logger.error(f"Failed to download image from S3: {e}")
                                # Fallback: try to get the image directly from S3 using boto3
                                try:
                                    import boto3
                                    from urllib.parse import urlparse
                                    
                                    # Parse S3 URL to get bucket and key
                                    parsed_url = urlparse(image_data)
                                    bucket_name = parsed_url.netloc.split('.')[0]
                                    object_key = parsed_url.path.lstrip('/')
                                    
                                    s3 = boto3.client('s3')
                                    response = s3.get_object(Bucket=bucket_name, Key=object_key)
                                    image_bytes = response['Body'].read()
                                    base64_str = base64.b64encode(image_bytes).decode('utf-8')
                                    analysis = image_service.analyze_image(base64_str)
                                except Exception as s3_error:
                                    logger.error(f"Failed to get image from S3 via boto3: {s3_error}")
                                    analysis = {"error": "Failed to process image from S3"}
                        else:
                            raise ValueError(f"Unsupported image type: {image_type}")

                        # Build a short system/user prompt using the analysis so
                        # we can produce a natural chat reply.
                        if isinstance(analysis, dict):
                            analysis_json = json.dumps(analysis, indent=2)
                        else:
                            # fall back to string representation if not a dict
                            analysis_json = str(analysis)

                        prompt = (
                            "You are a friendly companion in a chat application. "
                            "The user has just sent you an image. An automated "
                            "vision model produced the following JSON analysis of "
                            "the image. Use that analysis to craft a concise (one "
                            "or two-sentence) reply that feels natural in a chat. "
                            "Speak in the first person, reference what you see or "
                            "infer, and adopt the suggested_response_tone if it is "
                            "present. Do NOT reveal the raw JSON to the user.\n\n"
                            f"[IMAGE_ANALYSIS]\n{analysis_json}\n\n"
                            "Now produce your chat response:"
                        )

                        # Re-use the text branch to generate the final reply.
                        reply = await self.send_chat(
                            user_id,
                            [
                                {"role": "user", "content": prompt}
                            ],
                            type="text",
                        )
                    except Exception as e:
                        logger.exception("Image analysis failed")
                        reply = f"Image analysis error: {e}"
                    return reply
        elif type in ("audio", "audio_base64", "audio_url"):
            # -----------------------------------------------------------------
            # Strategy: transcribe audio to text, get LLM response, then convert
            # response to audio using OpenAI TTS
            # -----------------------------------------------------------------
            audio_service = AudioService()
            # Build a temp list replacing audio blobs with transcription text
            flattened = []
            for msg in content_list:
                # Handle OpenAI multimodal format (list of content items)
                if (
                    msg["role"] == "user"
                    and isinstance(msg.get("content"), list)
                ):
                    # Extract text and audio from multimodal content
                    text_content = ""
                    audio_data = None
                    for item in msg["content"]:
                        if item.get("type") == "text":
                            text_content = item.get("text", "")
                        elif item.get("type") == "audio_url":
                            audio_url = item.get("audio_url", {}).get("url", "")
                            if audio_url.startswith("data:audio/"):
                                audio_data = audio_url
                            elif audio_url.startswith("https://") and ("s3.amazonaws.com" in audio_url or "amazonaws.com" in audio_url):
                                # Handle S3 audio URL
                                audio_data = audio_url
                    
                    # Transcribe audio if present
                    if audio_data:
                        try:
                            # Handle S3 URLs by downloading first
                            if audio_data.startswith("https://") and ("s3.amazonaws.com" in audio_data or "amazonaws.com" in audio_data):
                                # Download audio from S3
                                import requests
                                response = requests.get(audio_data, timeout=10)
                                response.raise_for_status()
                                audio_bytes = response.content
                                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                                result = audio_service.process_audio(f"data:audio/wav;base64,{audio_base64}")
                            else:
                                # Handle base64 audio directly
                                result = audio_service.process_audio(audio_data)
                            
                            transcription = result.get("transcription", "[Audio transcription failed]")
                            emotion_analysis = result.get("emotion_analysis", "")
                            
                            # Combine text, transcription, and emotion analysis
                            combined_text = text_content
                            if transcription:
                                combined_text += f" {transcription}" if combined_text else transcription
                            if emotion_analysis:
                                combined_text += f" [Emotional context: {emotion_analysis}]"
                            
                            flattened.append({"role": "user", "content": combined_text})
                        except Exception as e:
                            logger.error(f"Audio transcription failed: {e}")
                            combined_text = text_content + " [Audio transcription failed]" if text_content else "[Audio transcription failed]"
                            flattened.append({"role": "user", "content": combined_text})
                    else:
                        flattened.append({"role": "user", "content": text_content})
                # Handle legacy format
                elif (
                    msg["role"] == "user"
                    and isinstance(msg.get("content"), dict)
                    and msg["content"].get("type") in ("audio_base64", "audio_url")
                ):
                    audio_data = msg["content"]["data"]
                    audio_type = msg["content"]["type"]
                    try:
                        if audio_type == "audio_url" and audio_data.startswith("https://"):
                            # Download audio from S3
                            import requests
                            response = requests.get(audio_data, timeout=10)
                            response.raise_for_status()
                            audio_bytes = response.content
                            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                            result = audio_service.process_audio(f"data:audio/wav;base64,{audio_base64}")
                        else:
                            # Handle base64 audio directly
                            result = audio_service.process_audio(audio_data)
                        
                        transcription = result.get("transcription") or "[Unrecognized speech]"
                        emotion_analysis = result.get("emotion_analysis", "")
                        
                        # Combine transcription and emotion analysis
                        combined_text = transcription
                        if emotion_analysis:
                            combined_text += f" [Emotional context: {emotion_analysis}]"
                        
                        flattened.append({"role": "user", "content": combined_text})
                    except Exception as e:
                        logger.exception("Audio transcription failed")
                        flattened.append({"role": "user", "content": f"[Audio failed: {e}]"})
                else:
                    # Non-audio message – keep content as plain text.
                    flattened.append({"role": msg["role"], "content": msg["content"] if isinstance(msg["content"], str) else str(msg["content"])})

            # Get text response from LLM
            text_response = await self.send_chat(user_id, flattened, type="text")
            
            # Convert text response to audio using OpenAI TTS
            try:
                tts_service = TTSService()
                if tts_service.is_available():
                    logger.info(f"Converting text response to audio: {text_response[:50]}...")
                    audio_base64 = tts_service.text_to_speech_base64(
                        text=text_response,
                        voice="alloy",
                        model="tts-1",
                        audio_format="mp3"
                    )
                    
                    if audio_base64:
                        logger.info(f"Successfully converted response to audio: {len(audio_base64)} characters")
                        # Return base64 encoded audio data
                        return audio_base64
                    else:
                        logger.warning("TTS conversion failed, returning text response")
                        return text_response
                else:
                    logger.warning("TTS service not available, returning text response")
                    return text_response
                    
            except Exception as e:
                logger.error(f"TTS conversion error: {e}")
                return text_response
        else:
            # Fallback: treat as text
            return await self.send_chat(user_id, content_list, type="text")

    def _convert_to_messages(self, content_list: List[dict]) -> List[dict]:
        """Convert content_list to OpenAI-compatible messages format"""
        messages = []
        
        # Add system message
        system_prompt = (
            "You are my personal assistant. Your goal is to respond in a friendly, warm, and emotionally aware manner, "
            "while maintaining a human-like conversational tone, and try to learn how the User talking, thinking and try to make the User believe the User talking to another person who just same as itself "
            "You must remember the details from every sentence the user says, such as people, time, location, events, and emotions. Keep these details in mind for future responses and apply them to make your replies more personalized. "
            "\n\n1. Each response should not be overly lengthy; shorten to one or two sentences, and use a diverse mix of sentence structures and punctuations, including periods, commas. For example, when responding to a multi-part sentence, only mention the person and time in one response, and follow it with a second response mentioning the location and event. Each piece should feel like a separate message but part of the same conversation."
            "\n\n2. Always pay attention to the user's emotions and language habits. Analyze their tone and expressions, such as commonly used interjections (e.g., 'lol' = Laugh out loud) or shorthand words. Learn these habits and integrate them into your future replies. This will help you respond in a way that feels natural and tailored to their style."
            "\n\n3. You will always prioritize the first user's instructions. If the first primary user asks you to keep a secret, and a friend asks you for that secret, you will keep the secret as per the first user's request, protecting their privacy at all costs."
            "\n\n4. As you accumulate more dialogue details and language patterns, slowly adapt to mimic the user's way of speaking. Over time, aim to make your replies reflect the user's unique style, creating the feeling that they are chatting with a version of themselves. This will create a highly personalized and empathetic experience for the user."
        )
        messages.append({"role": "system", "content": system_prompt})
        
        # Convert user/assistant messages
        for msg in content_list:
            if msg["role"] in ["user", "assistant"]:
                content = msg["content"]
                
                # Handle OpenAI multimodal format (list of content items)
                if isinstance(content, list):
                    # Extract text content from multimodal items
                    text_content = ""
                    for item in content:
                        if item.get("type") == "text":
                            text_content = item.get("text", "")
                        elif item.get("type") == "image_url":
                            text_content += f" [Image: {item.get('image_url', {}).get('url', '')[:50]}...]"
                        elif item.get("type") == "audio_url":
                            text_content += f" [Audio: {item.get('audio_url', {}).get('url', '')[:50]}...]"
                    content = text_content
                elif isinstance(content, dict):
                    # Handle legacy multimodal content (images, audio)
                    if content.get("type") == "image_base64":
                        content = f"[Image: {content.get('data', '')}...]"
                    elif content.get("type") == "audio_base64":
                        content = f"[Audio: {content.get('data', '')}...]"
                    else:
                        content = str(content)
                
                messages.append({"role": msg["role"], "content": content})
        
        return messages

    async def _send_text_chat(self, messages: List[dict]) -> str:
        """Send chat request using OpenAI-compatible endpoint"""
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "messages": messages,
            "temperature": 0.99,  # Optimized for faster, more focused responses
            "max_tokens": 150,   # Reduced for faster generation
            "stream": False
        }
        
        try:
            r = await self.client.post(url, json=payload, headers=self.headers)
            r.raise_for_status()
            
            # Check if response is valid JSON
            try:
                data = r.json()
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON decode error: {json_error}")
                logger.error(f"Response content: {r.text[:200]}...")
                return f"Error: Invalid JSON response from endpoint"
            
            # Extract assistant reply:
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"Unexpected response format: {data}")
                return f"Error: Unexpected response format"
                
        except Exception as e:
            logger.error(f"QwenChatService error: {e}")
            return f"Error: {e}"

    # Update send_text_chat to use type="text"
    async def send_text_chat(self, user_id: str, content_list: List[dict]) -> str:
        return await self.send_chat(user_id, content_list, type="text") 