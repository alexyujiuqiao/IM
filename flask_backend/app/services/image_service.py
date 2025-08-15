import base64
from io import BytesIO
from PIL import Image
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"), base_url=os.getenv("DASHSCOPE_BASE_URL"))

class ImageService:
    def __init__(self):
        self.model = "qwen-vl-max"
    
    def analyze_image(self, image_data: str) -> Dict:
        """
        Analyze an image for emotional content and scene understanding.
        image_data should be a base64 encoded string of the image.
        """
        try:
            
            # Prepare the image for Qwen-VL-Max Vision
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this image using advanced emotional tone analysis and provide a detailed response in JSON format with these fields:
                                
                                - emotional_tone: Choose from this comprehensive emotion list:
                                  * Joy/Happiness: delighted, cheerful, enthusiastic, satisfied, grateful
                                  * Sadness: disappointed, frustrated, melancholy, regretful, hopeless
                                  * Anger: irritated, annoyed, furious, resentful, hostile
                                  * Fear: anxious, worried, scared, nervous, panicked
                                  * Surprise: shocked, amazed, astonished, bewildered, stunned
                                  * Disgust: repulsed, revolted, appalled, contemptuous, disdainful
                                  * Trust: confident, secure, trusting, hopeful, optimistic
                                  * Anticipation: excited, eager, curious, interested, expectant
                                  * Love: affectionate, caring, warm, tender, loving
                                  * Contempt: scornful, dismissive, condescending, arrogant, superior
                                  * Confusion: puzzled, uncertain, doubtful, conflicted, indecisive
                                  * Relief: relaxed, calm, peaceful, content, at ease
                                
                                - secondary_emotions: List of 2-3 additional emotions present in the image
                                - primary_subjects: list of main subjects/objects
                                - scene_description: detailed description of the scene
                                - emotional_intensity: number from 1-5 indicating emotional intensity (1=very mild, 5=very intense)
                                - emotional_complexity: number from 1-3 indicating how complex the emotional state is (1=single emotion, 3=very complex mix)
                                - color_mood: description of how colors contribute to the mood
                                - visual_elements: list of visual elements that contribute to the emotional tone (lighting, composition, expressions, etc.)
                                - suggested_response_tone: how the chatbot should respond to this image (empathetic, supportive, celebratory, calming, etc.)
                                - emotional_triggers: potential causes or triggers for the detected emotions in the image
                                - response_urgency: number from 1-3 indicating how urgently the emotion needs addressing (1=low, 3=high)"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Parse the response
            analysis = response.choices[0].message.content
            return self._parse_analysis(analysis)
            
        except Exception as e:
            print(f"Error analyzing image: {str(e)}")
            return {
                "error": str(e),
                "emotional_tone": "neutral",
                "emotional_intensity": 3
            }
    
    def _parse_analysis(self, analysis: str) -> Dict:
        """Parse the GPT-4 Vision analysis into a structured format"""
        try:
            # Clean up the response and parse as JSON
            import json
            import re
            
            # Remove markdown code blocks if present
            analysis = re.sub(r"```json|```", "", analysis).strip()
            
            # Parse the JSON response
            result = json.loads(analysis)
            
            # Ensure all required fields are present
            required_fields = [
                "emotional_tone",
                "secondary_emotions",
                "primary_subjects",
                "scene_description",
                "emotional_intensity",
                "emotional_complexity",
                "color_mood",
                "visual_elements",
                "suggested_response_tone",
                "emotional_triggers",
                "response_urgency"
            ]
            
            for field in required_fields:
                if field not in result:
                    result[field] = "unknown"
            
            return result
            
        except Exception as e:
            print(f"Error parsing analysis: {str(e)}")
            return {
                "error": "Failed to parse analysis",
                "emotional_tone": "neutral",
                "secondary_emotions": [],
                "emotional_intensity": 3,
                "emotional_complexity": 1,
                "visual_elements": [],
                "emotional_triggers": [],
                "response_urgency": 1
            }
    
    def get_emotional_context(self, analysis: Dict) -> Tuple[str, int]:
        """Extract emotional context from image analysis"""
        return (
            analysis.get("emotional_tone", "neutral"),
            analysis.get("emotional_intensity", 3)
        )
    
    def get_scene_context(self, analysis: Dict) -> str:
        """Get a natural language description of the scene"""
        subjects = ", ".join(analysis.get("primary_subjects", []))
        description = analysis.get("scene_description", "")
        return f"The image shows {subjects}. {description}"
