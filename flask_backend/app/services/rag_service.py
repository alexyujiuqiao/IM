import os
import json
import logging
from datetime import datetime
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv
from .qwen_chat_service import QwenChatService
from .memory_service import MemoryService
import asyncio
import re
import concurrent.futures

load_dotenv()
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class RAGService:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(os.getenv("PINECONE_INDEX_NAME"))
        self._qwen_service = None
        self._memory_service = None
        # Voice profile mapping for prompt styles
        self.voice_profile_prompts = {
            "魅力女友": "Respond in a charming and playful girlfriend tone, using sweet expressions and light humor.",
            "柔美女友": "Respond in a gentle, caring tone, softly comforting and encouraging the user.",
            "傲娇霸总": "Respond in a confident, slightly teasing CEO-like tone with a hint of tsundere warmth underneath.",
            "正直青年": "Respond in a straightforward, righteous young male tone, honest and spirited."
        }

    @property
    def qwen_service(self):
        if self._qwen_service is None:
            self._qwen_service = QwenChatService()
        return self._qwen_service

    @property
    def memory_service(self):
        if self._memory_service is None:
            self._memory_service = MemoryService()
        return self._memory_service

    def extract_key_info(self, text, conversation_context=""):
        """Extract key information from the user message in a single sentence format."""
        context_prompt = ""
        if conversation_context:
            context_prompt = f"\n\nConversation Context: {conversation_context}"
        
        # Check if the text contains emotional context from audio analysis
        emotional_context = ""
        if "[Emotional context:" in text:
            # Extract emotional context from the text
            start_idx = text.find("[Emotional context:")
            end_idx = text.find("]", start_idx)
            if end_idx != -1:
                emotional_context = text[start_idx + 19:end_idx].strip()
                # Remove the emotional context from the main text for processing
                text = text[:start_idx].strip() + text[end_idx + 1:].strip()
        
        emotion_prompt = ""
        if emotional_context:
            emotion_prompt = f"\n\nEmotional Context: {emotional_context}"
        
        prompt = (
            f"Extract key information from the user message and summarize it in ONE natural sentence. "
            f"Include: who (people mentioned), what (main event/action), when (time references), "
            f"where (locations), why (purpose/intent), and emotional state. "
            f"Make it conversational and natural, like you're describing what the user said to someone else.{context_prompt}{emotion_prompt}\n\n"
            f"User message: {text}\n\n"
            f"Extracted information (one sentence):"
        )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        print("[DEBUG] Raw LLM output:", repr(content))  # Debug print
        
        # Return the single sentence directly
        return {"extracted_info": content}

    def rephrase_query_with_context(self, query, conversation_history):
        """Rephrase user query using conversation history for better retrieval."""
        if not conversation_history:
            return query
        
        # Build conversation context for rephrasing
        context_parts = []
        for msg in conversation_history[-4:]:  # Last 4 messages for context
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if role == 'user':
                context_parts.append(f"User: {content}")
            elif role == 'assistant':
                context_parts.append(f"Assistant: {content}")
        
        conversation_context = "\n".join(context_parts)
        
        prompt = f"""Rewrite the question for search while keeping its meaning and key terms intact.
        If the conversation history is empty, DO NOT change the query.
        Use conversation history only if necessary, and avoid extending the query with your own knowledge.
        If no changes are needed, output the current question as is.

        Conversation history:
        {conversation_context}

        User Query: {query}
        Rewritten Query:"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0
            )
            rephrased_query = response.choices[0].message.content.strip()
            logger.info(f"Query rephrased: '{query}' -> '{rephrased_query}'")
            return rephrased_query
        except Exception as e:
            logger.error(f"Error rephrasing query: {e}")
            return query

    def get_embedding(self, text):
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
        return response.data[0].embedding

    def _build_conversation_context(self, chat_history):
        """Build a concise context from recent chat history."""
        if not chat_history:
            return ""
        
        # Take last 3 Q&A pairs for context
        recent_messages = chat_history[-6:] if len(chat_history) > 6 else chat_history
        
        context_parts = []
        for i in range(0, len(recent_messages), 2):
            if i + 1 < len(recent_messages):
                user_msg = recent_messages[i].get('content', '')
                assistant_msg = recent_messages[i + 1].get('content', '')
                context_parts.append(f"User: {user_msg}\nAssistant: {assistant_msg}")
        
        return "\n".join(context_parts)

    def _build_relevant_context(self, user_id, current_message):
        """Build relevant context from multiple recent extractions."""
        try:
            # Get multiple recent extractions to build relevant context
            extracted_infos = self.retrieve_extracted_info(user_id, top_k=5)
            
            if not extracted_infos:
                return "No previous context available."
            
            # Build relevant context from recent extractions
            context_parts = []
            for info in extracted_infos:
                if 'extracted_info' in info and info['extracted_info']:
                    context_parts.append(info['extracted_info'])
            
            if context_parts:
                return "Relevant Context:\n" + "\n".join(f"• {part}" for part in context_parts)
            else:
                return "Relevant Context: Limited information available."
                
        except Exception as e:
            logger.error(f"Error building relevant context: {e}")
            return "Relevant Context: Error retrieving context information."

    def _retrieve_semantic_context(self, user_id, current_message):
        """Retrieve context relevant to the current message using semantic search."""
        try:
            # Use the current message to find relevant context
            query_embedding = self.get_embedding(current_message)
            
            results = self.index.query(
                vector=query_embedding,
                top_k=3,
                include_metadata=True,
                filter={"user_id": user_id, "type": "extracted_info"}
            )
            
            if results['matches']:
                semantic_parts = []
                for match in results['matches']:
                    if match['score'] > 0.7:  # Only use highly relevant matches
                        metadata = match['metadata']
                        if 'extracted_info' in metadata:
                            semantic_parts.append(metadata['extracted_info'])
                
                if semantic_parts:
                    return "Semantic Context:\n" + "\n".join(f"• {part}" for part in semantic_parts)
            
            return "Semantic Context: No specific context found for this message."
            
        except Exception as e:
            logger.error(f"Error retrieving semantic context: {e}")
            return "Semantic Context: Error retrieving context."

    def _build_enhanced_prompt(self, relevant_context, semantic_context, chat_history, user_message, voice_profile_prompt=""):
        """Build an enhanced prompt with proper structure and instructions."""
        
        # Format chat history for better readability
        formatted_history = ""
        if chat_history:
            history_parts = []
            for msg in chat_history[-4:]:  # Last 4 messages
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                if role == 'user':
                    history_parts.append(f"User: {content}")
                elif role == 'assistant':
                    history_parts.append(f"Assistant: {content}")
            
            formatted_history = "\n".join(history_parts)
        
        prompt = f"""You are a helpful AI assistant with access to conversation context and history.

            {relevant_context}

            {semantic_context}

            Recent Conversation:
            {formatted_history}

            Current User Message:
            {user_message}

            Instructions:
            1. Use the relevant context to provide personalized responses
            2. Reference semantic context when appropriate for better understanding
            3. Maintain conversation continuity and flow
            4. Be helpful, empathetic, and engaging
            5. If the user asks about something you don't know, say so rather than guessing

            {voice_profile_prompt}

            Your response:"""
        
        return prompt

    def _build_enhanced_prompt_with_memory(self, memory_context, memory_summary, user_profile, relevant_context, semantic_context, chat_history, user_message, voice_profile_prompt):
        """Build an enhanced prompt that includes memory context and voice style."""
        
        # Format chat history for better readability
        formatted_history = ""
        if chat_history:
            history_parts = []
            for msg in chat_history[-4:]:  # Last 4 messages
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                if role == 'user':
                    history_parts.append(f"User: {content}")
                elif role == 'assistant':
                    history_parts.append(f"Assistant: {content}")
            
            formatted_history = "\n".join(history_parts)
        
        prompt = f"""You are a helpful AI assistant with access to conversation context, memory, and history.

            Memory Context:
            {memory_context}

            Memory Summary:
            {memory_summary}

            User Profile:
            {user_profile}

            {relevant_context}

            {semantic_context}

            Recent Conversation:
            {formatted_history}

            Current User Message:
            {user_message}

            Instructions:
            1. Use the relevant context and memory to provide personalized responses
            2. Reference semantic context when appropriate for better understanding
            3. Maintain conversation continuity and flow
            4. Be helpful, empathetic, and engaging
            5. If the user asks about something you don't know, say so rather than guessing

            {voice_profile_prompt}

            Your response:"""
        
        return prompt


    def add_extracted_info_to_vector_db(self, user_id, extracted_info, timestamp=None):
        """Store extracted info in Pinecone for session/memory."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # We now only use the new single sentence format
        if 'extracted_info' in extracted_info:
            info_text = extracted_info['extracted_info']
            metadata = {
                "extracted_info": info_text,
                "text": info_text,
                "type": "extracted_info",
                "user_id": user_id,
                "timestamp": timestamp
            }
        else:
            # Fallback: convert to string if somehow we get old format
            logger.warning(f"Received old format extracted_info: {extracted_info}")
            info_text = str(extracted_info)
            metadata = {
                "extracted_info": info_text,
                "text": info_text,
                "type": "extracted_info",
                "user_id": user_id,
                "timestamp": timestamp
            }
        try:
            embedding = self.get_embedding(info_text)
            vector_id = f"{user_id}_{timestamp}_extracted"
            self.index.upsert(vectors=[(vector_id, embedding, metadata)])
            logger.info("Extracted info upserted to Pinecone")
            return True
        except Exception as e:
            logger.error(f"Error upserting extracted info: {e}")
            return False

    def add_voice_profile_to_vector_db(self, user_id, voice_profile_name, timestamp=None):
        """Store or update the user's preferred voice profile in Pinecone."""
        if not voice_profile_name:
            return False
        if timestamp is None:
            from datetime import datetime
            timestamp = datetime.now().isoformat()
        metadata = {
            "voice_profile": voice_profile_name,
            "text": f"voice_profile::{voice_profile_name}",
            "type": "voice_profile",
            "user_id": user_id,
            "timestamp": timestamp
        }
        try:
            embedding = self.get_embedding(metadata["text"])
            vector_id = f"{user_id}_voice_profile"
            self.index.upsert(vectors=[(vector_id, embedding, metadata)])
            logger.info("Voice profile upserted to Pinecone")
            return True
        except Exception as e:
            logger.error(f"Error upserting voice profile: {e}")
            return False

    def retrieve_extracted_info(self, user_id, top_k=5):
        """Retrieve recent extracted info for a user from Pinecone."""
        try:
            query_text = f"user {user_id} extracted info"
            embedding = self.get_embedding(query_text)
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"user_id": user_id, "type": "extracted_info"}
            )
            if results['matches']:
                # Sort by timestamp descending
                sorted_matches = sorted(results['matches'], key=lambda x: x['metadata']['timestamp'], reverse=True)
                result_list = []
                for match in sorted_matches:
                    metadata = match['metadata']
                    
                    # Handle both new and old formats
                    if 'extracted_info' in metadata:
                        # New format: single sentence
                        result = {
                            "extracted_info": metadata['extracted_info'],
                            "timestamp": metadata['timestamp']
                        }
                    else:
                        # Old format: JSON fields
                        allowed = {"person", "when", "where", "event", "emotions", "timestamp"}
                        result = {k: v for k, v in metadata.items() if k in allowed}
                        
                        # Parse emotions JSON string back to dict
                        if "emotions" in result and isinstance(result["emotions"], str):
                            try:
                                result["emotions"] = json.loads(result["emotions"])
                            except json.JSONDecodeError:
                                logger.warning("Failed to parse emotions JSON string")
                    
                    result_list.append(result)
                
                return result_list
            return []
        except Exception as e:
            logger.error(f"Error retrieving extracted info: {e}")
            return []

    def _generate_multiqueries(self, query, n=3):
        """Generate multiple rephrasings of the user query using LLM."""
        # For simplicity, use prompt engineering to get n rephrasings
        prompt = (
            f"Rephrase the following question in {n} different ways, keeping the meaning the same.\n"
            f"Question: {query}\n"
            f"Rephrasings (one per line):"
        )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.7
        )
        lines = response.choices[0].message.content.strip().split("\n")
        queries = [query] + [line.strip("- ") for line in lines if line.strip()]
        return queries[:n]

    def _reciprocal_rank_fusion(self, results_lists, k=5):
        """Fuse multiple ranked lists using Reciprocal Rank Fusion (RRF)."""
        # results_lists: list of lists of Pinecone matches
        scores = {}
        for result_list in results_lists:
            for rank, match in enumerate(result_list):
                doc_id = match['id']
                # RRF score: 1 / (k + rank)
                scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
        # Sort by RRF score
        sorted_ids = sorted(scores, key=scores.get, reverse=True)
        # Flatten and deduplicate matches by doc_id
        id_to_match = {m['id']: m for l in results_lists for m in l}
        fused = [id_to_match[doc_id] for doc_id in sorted_ids]
        return fused[:k]

    def retrieve_context(self, query, user_id, top_k=5, filters=None, multiquery_n=3):
        """Improved retrieval: multiquery + RRF + hierarchical chunking (parent/child swap)."""
        # 1. Generate multiqueries
        queries = self._generate_multiqueries(query, n=multiquery_n)
        # 2. For each query, embed and search Pinecone
        pinecone_filter = {"user_id": user_id}
        if filters:
            pinecone_filter.update(filters)
        results_lists = []
        for q in queries:
            embedding = self.get_embedding(q)
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter=pinecone_filter
            )
            results_lists.append(results['matches'])
        # 3. Fuse results using RRF
        fused = self._reciprocal_rank_fusion(results_lists, k=top_k)
        # 4. Hierarchical chunking: swap to parent if enough children are present
        # (Assume metadata has 'parent_id' and 'parent_text' if using hierarchical chunking)
        parent_counts = {}
        parent_texts = {}
        for match in fused:
            parent_id = match['metadata'].get('parent_id')
            if parent_id:
                parent_counts[parent_id] = parent_counts.get(parent_id, 0) + 1
                parent_texts[parent_id] = match['metadata'].get('parent_text')
        # If >= half of top_k are from the same parent, swap to parent chunk
        for parent_id, count in parent_counts.items():
            if count >= top_k // 2 and parent_id in parent_texts:
                # Replace all child chunks with the parent chunk
                return [parent_texts[parent_id]]
        # Otherwise, return the best child chunks
        return [m['metadata']['text'] for m in fused]

    def classify_voice_profile_from_text(self, text: str) -> str:
        """Classify the best voice profile just from text sentiment/emotion."""
        try:
            prompt = (
                "You are an emotion classifier that maps user text to one of four profiles: "
                "魅力女友 (charming girlfriend, playful, sweet), "
                "柔美女友 (gentle girlfriend, caring, soft), "
                "傲娇霸总 (tsundere CEO, confident, teasing), "
                "正直青年 (upright young man, honest, spirited).\n\n"
                "Read the USER_TEXT delimited by triple backticks and output ONLY the profile name that best fits.\n"
                "If unsure choose 正直青年.\n\n"
                "```\n" + text + "\n```"
            )
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0
            )
            profile = response.choices[0].message.content.strip().split()[0]
            if profile in self.voice_profile_prompts:
                return profile
            # Try fallback mapping via heuristics
            return "正直青年"
        except Exception as e:
            logger.error(f"Voice profile classification failed: {e}")
            return "正直青年"

    def rag_pipeline(self, user_id, user_message, chat_history, input_type="text", content=None):
        # NEW: Memory Service Integration (Step 1)
        logger.info(f"Starting enhanced RAG pipeline with memory for user: {user_id}")
        
        # Process conversation through memory service first
        try:
            # Prepare messages for memory processing
            memory_messages = []
            if chat_history:
                memory_messages.extend(chat_history)
            memory_messages.append({"role": "user", "content": user_message})
            
            # Process through memory graph
            memory_result = self.memory_service.process_conversation(user_id, memory_messages)
            
            # Get enhanced context from memory
            memory_context = memory_result.get("context", "")
            user_profile = memory_result.get("user_profile", {})
            memory_summary = memory_result.get("memory_summary", "")
            
            logger.info(f"Memory processing completed for user: {user_id}")
            logger.info(f"Memory context length: {len(memory_context)}")
            logger.info(f"User profile keys: {list(user_profile.keys()) if user_profile else 'None'}")
            
        except Exception as e:
            logger.error(f"Memory service processing failed: {e}")
            memory_context = ""
            user_profile = {}
            memory_summary = ""
        
        # Handle audio input specifically
        voice_profile_prompt = ""
        voice_profile_name = None
        if input_type == "audio" and content:
            # For audio input, we need to process the audio content first
            try:
                from .audio_service import AudioService
                audio_service = AudioService()
                
                # Process the audio content
                if isinstance(content, dict) and content.get("type") == "audio_base64":
                    audio_data = content.get("data", "")
                elif isinstance(content, str):
                    audio_data = content
                else:
                    audio_data = str(content)
                
                # Process audio to get transcription and emotion
                result = audio_service.process_audio(audio_data)
                transcription = result.get("transcription", "")
                emotion_analysis = result.get("emotion_analysis", "")
                voice_profile_name = result.get("voice_profile_name")
                # Store voice profile for future use
                self.add_voice_profile_to_vector_db(user_id, voice_profile_name)
                # Prepare style prompt if mapping exists
                if voice_profile_name and voice_profile_name in self.voice_profile_prompts:
                    voice_profile_prompt = self.voice_profile_prompts[voice_profile_name]
                
                # Use transcription as the main message for extraction
                if transcription:
                    user_message = transcription
                    if emotion_analysis:
                        user_message += f" [Emotional context: {emotion_analysis}]"
                else:
                    user_message = "[Audio transcription failed]"
                    
                logger.info(f"Audio processed - Transcription: {transcription}")
                logger.info(f"Audio processed - Emotion: {emotion_analysis}")
                
            except Exception as e:
                logger.error(f"Error processing audio in RAG pipeline: {e}")
                user_message = "[Audio processing failed]"
        elif input_type == "text":
            # Attempt to classify voice profile from text emotion
            voice_profile_name = self.classify_voice_profile_from_text(user_message)
            self.add_voice_profile_to_vector_db(user_id, voice_profile_name)
            if voice_profile_name in self.voice_profile_prompts:
                voice_profile_prompt = self.voice_profile_prompts[voice_profile_name]
        
        # NEW: Query Rephrasing (Step 2) - Following Haystack pattern
        rephrased_query = self.rephrase_query_with_context(user_message, chat_history)
        logger.info(f"Query rephrased: '{user_message}' -> '{rephrased_query}'")
        
        # 1. Extract key info from the message with conversation context
        conversation_context = self._build_conversation_context(chat_history)
        extracted = self.extract_key_info(user_message, conversation_context)
        logger.info(f"Extracted info from {input_type} input: {extracted}")
        
        # 2. Store in Pinecone (only as extracted info)
        self.add_extracted_info_to_vector_db(user_id, extracted)
        
        # 3. Build relevant context from multiple recent extractions
        relevant_context = self._build_relevant_context(user_id, rephrased_query)  # Use rephrased query
        
        # 4. Retrieve additional semantic context based on current message
        semantic_context = self._retrieve_semantic_context(user_id, rephrased_query)  # Use rephrased query
        
        # 5. Build enhanced prompt with memory context (now includes memory + voice style)
        prompt = self._build_enhanced_prompt_with_memory(
            memory_context, memory_summary, user_profile, 
            relevant_context, semantic_context, chat_history, user_message, voice_profile_prompt
        )
        
        # 6. Call LLM
        if input_type == "text" or input_type == "audio":
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            llm_response = loop.run_until_complete(self.qwen_service.send_chat(
                user_id, [{"role": "user", "content": prompt}], type="text"
            ))
            loop.close()
            
            # NEW: Store conversation in memory after LLM response
            try:
                # Add the assistant response to memory
                full_conversation = memory_messages + [{"role": "assistant", "content": llm_response}]
                self.memory_service.process_conversation(user_id, full_conversation)
                logger.info(f"Conversation stored in memory for user: {user_id}")
            except Exception as e:
                logger.error(f"Failed to store conversation in memory: {e}")
            
            return llm_response, voice_profile_name
        else:
            # For other multimodal types (image), pass through
            content_list = []
            if chat_history:
                for msg in chat_history:
                    content_list.append(msg)
            if input_type.startswith("image") and content:
                content_list.append({"role": "user", "content": content})
            elif user_message:
                content_list.append({"role": "user", "content": user_message})
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            llm_response = loop.run_until_complete(self.qwen_service.send_chat(
                user_id, content_list, type=input_type
            ))
            loop.close()
            return llm_response, voice_profile_name
