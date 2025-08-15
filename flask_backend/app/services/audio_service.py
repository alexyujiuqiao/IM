import base64
from io import BytesIO
from openai import OpenAI
from typing import Dict, Tuple, Optional
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

class AudioService:
    def __init__(self):
        self.speech_model = "whisper-1"
        self.analysis_model = "qwen-max"  # Use qwen-plus for emotion analysis (confirmed working in DashScope)
        self.openai_client = OpenAI()  # Initialize the new OpenAI client
        self.qwen_client = OpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"), base_url=os.getenv("DASHSCOPE_BASE_URL"))
        self._voice_profile_map = {
            "7426720361733013513": "魅力女友",  # Charming Girlfriend
            "7426720361733046281": "柔美女友",  # Gentle Girlfriend
            "7426720361733210121": "傲娇霸总",  # Tsundere CEO
            "7468518846874271795": "正直青年"   # Righteous Youth
        }
    
    def process_audio(self, audio_data: str) -> Dict:
        """
        Process audio data for transcription and emotional analysis.
        audio_data should be a base64 encoded string of the audio file.
        """
        try:
            # First, transcribe the audio
            transcription = self._transcribe_audio(audio_data)
            if not transcription:
                return {
                    "error": "Failed to transcribe audio",
                    "transcription": None,
                    "emotion_analysis": None
                }
            
            # Then analyze the emotional content
            emotion_analysis = self._analyze_emotion(transcription)
            if not emotion_analysis:
                emotion_analysis = "The speaker's emotional state appears neutral with no strong emotional indicators detected."
            
            # Combine results
            return {
                "transcription": transcription,
                "emotion_analysis": emotion_analysis,
                "voice_profile_id": self._classify_voice_profile(emotion_analysis),
                "voice_profile_name": self._voice_profile_map.get(self._classify_voice_profile(emotion_analysis)),
                "error": None
            }
            
        except Exception as e:
            print(f"Error processing audio: {str(e)}")
            return {
                "error": str(e),
                "transcription": None,
                "emotion_analysis": None
            }
    
    def _transcribe_audio(self, audio_data: str) -> Optional[str]:
        """Transcribe audio using Whisper API"""
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Create a temporary file-like object
            audio_file = BytesIO(audio_bytes)
            audio_file.name = "audio.wav"  # Whisper needs a filename
            
            # Call Whisper API using the new client
            response = self.openai_client.audio.transcriptions.create(
                model=self.speech_model,
                file=audio_file,
                response_format="text"
            )
            
            return response
            
        except Exception as e:
            print(f"Error transcribing audio: {str(e)}")
            return None
    
    def _analyze_emotion(self, text: str) -> Optional[str]:
        """Analyze emotional content of transcribed text and return a simple summary sentence"""
        try:
            prompt = f"""
                Analyze the emotional content of this transcribed speech and provide a single natural sentence summary.
                
                The summary should include:
                - The primary emotion detected (joy, sadness, anger, fear, surprise, etc.)
                - Emotional intensity level (mild, moderate, strong)
                - Any notable speech patterns or emotional indicators
                - The overall emotional context
                
                Write this as a natural, conversational sentence that someone would use to describe the speaker's emotional state.
                
                Transcribed Text: "{text}"
                
                Emotional summary (one sentence):
                """
            
            response = self.qwen_client.chat.completions.create(
                model=self.analysis_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            
            # Return the simple sentence directly
            analysis = response.choices[0].message.content.strip()
            return analysis
            
        except Exception as e:
            print(f"Error analyzing emotion: {str(e)}")
            return "The speaker's emotional state appears neutral with no strong emotional indicators detected."
    
    def _classify_voice_profile(self, emotion_analysis: str) -> str:
        """Very rough heuristic mapping of emotion analysis to voice profile IDs."""
        if not emotion_analysis:
            return "7468518846874271795"  # default to Righteous Youth
        lower = emotion_analysis.lower()
        if any(word in lower for word in ["soft", "gentle", "caring", "tender"]):
            return "7426720361733046281"  # Gentle Girlfriend
        if any(word in lower for word in ["joy", "playful", "friendly", "charming", "sweet"]):
            return "7426720361733013513"  # Charming Girlfriend
        if any(word in lower for word in ["authoritative", "deep", "powerful", "boss", "commanding"]):
            return "7426720361733210121"  # Tsundere CEO
        return "7468518846874271795"  # fallback Righteous Youth
    

    

    

