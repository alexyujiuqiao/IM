import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from typing_extensions import TypedDict
import uuid

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class UserProfile(BaseModel):
    """User profile model for storing personal information"""
    name: Optional[str] = None
    age: Optional[int] = None
    profession: Optional[str] = None
    hobbies: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    personality_traits: List[str] = Field(default_factory=list)
    conversation_style: Optional[str] = None
    last_interaction: Optional[datetime] = None
    total_interactions: int = 0

class MemoryService:
    def __init__(self):
        """Initialize simplified memory service"""
        self.user_profiles: Dict[str, UserProfile] = {}
        self.conversation_histories: Dict[str, List[Dict]] = {}
        
    def process_conversation(self, user_id: str, messages: List[Dict]) -> Dict[str, Any]:
        """Process conversation and return context"""
        try:
            # Store conversation history
            if user_id not in self.conversation_histories:
                self.conversation_histories[user_id] = []
            
            self.conversation_histories[user_id].extend(messages)
            
            # Get or create user profile
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = UserProfile()
            
            profile = self.user_profiles[user_id]
            profile.total_interactions += 1
            profile.last_interaction = datetime.now()
            
            # Build context from recent conversations
            recent_messages = self.conversation_histories[user_id][-10:]  # Last 10 messages
            context = self._build_context_from_messages(recent_messages)
            
            return {
                "context": context,
                "user_profile": profile.dict(),
                "memory_summary": f"User has {profile.total_interactions} total interactions"
            }
            
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            return {
                "context": "",
                "user_profile": {},
                "memory_summary": ""
            }
    
    def _build_context_from_messages(self, messages: List[Dict]) -> str:
        """Build context from recent messages"""
        context_parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if isinstance(content, str):
                context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts[-5:])  # Last 5 messages
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile"""
        return self.user_profiles.get(user_id)
    
    def get_user_memory_summary(self, user_id: str) -> str:
        """Get memory summary for user"""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            return f"User has {profile.total_interactions} total interactions"
        return ""
    
    def clear_user_memory(self, user_id: str):
        """Clear all memory for a user"""
        if user_id in self.user_profiles:
            del self.user_profiles[user_id]
        if user_id in self.conversation_histories:
            del self.conversation_histories[user_id] 