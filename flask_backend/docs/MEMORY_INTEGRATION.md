# Memory Service Integration

This document describes the integration of the MemoryService with the RAG pipeline, following conversational RAG patterns from [Haystack's documentation](https://haystack.deepset.ai/cookbook/conversational_rag_using_memory).

## Overview

The MemoryService has been integrated into the RAG pipeline to provide enhanced conversational capabilities, user profiling, and memory management. This integration follows the conversational RAG pattern that includes:

1. **Memory Retrieval**: Getting relevant conversation history and user profile
2. **Query Rephrasing**: Improving search queries using conversation context
3. **Enhanced Context Building**: Combining memory with semantic search
4. **Memory Storage**: Storing conversations for future reference

## Architecture

### Components

- **MemoryService**: Handles user profiles, conversation memory, and memory graphs
- **RAGService**: Enhanced with memory integration and query rephrasing
- **Memory Endpoints**: API endpoints for memory management

### Integration Flow

```
User Message → Memory Processing → Query Rephrasing → Enhanced RAG → Memory Storage
     ↓              ↓                    ↓              ↓              ↓
  Input         Context Building    Better Search    LLM Response   Store Memory
```

## Key Features

### 1. Conversational Memory

The system now maintains conversation history and can reference previous interactions:

```python
# Memory processing provides enhanced context
memory_result = memory_service.process_conversation(user_id, messages)
memory_context = memory_result.get("context", "")
user_profile = memory_result.get("user_profile", {})
```

### 2. Query Rephrasing

Following the Haystack pattern, queries are rephrased using conversation history for better retrieval:

```python
# Example: "What's his name?" → "What's Einstein's name?"
rephrased_query = rag_service.rephrase_query_with_context(user_message, chat_history)
```

### 3. User Profiling

The system automatically extracts and maintains user profiles:

- **Name**: Extracted from conversation
- **Profession**: Job information
- **Hobbies**: Interests and activities
- **Personality Traits**: Conversation style and preferences
- **Interaction History**: Total interactions and last interaction time

### 4. Enhanced Prompt Building

Prompts now include memory context, user profile, and conversation history:

```python
prompt = rag_service._build_enhanced_prompt_with_memory(
    memory_context, memory_summary, user_profile,
    relevant_context, semantic_context, chat_history, user_message, voice_profile_prompt
)
```

## API Endpoints

### Memory Management

- `GET /api/chat/memory/profile/{user_id}` - Get user profile
- `POST /api/chat/memory/profile/{user_id}` - Update user profile
- `GET /api/chat/memory/summary/{user_id}` - Get conversation summary
- `DELETE /api/chat/memory/{user_id}` - Clear user memory

### Usage Examples

```bash
# Get user profile
curl -X GET "http://localhost:5000/api/chat/memory/profile/user123" \
  -H "Authorization: Bearer <token>"

# Update user profile
curl -X POST "http://localhost:5000/api/chat/memory/profile/user123" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "profession": "Engineer"}'

# Get memory summary
curl -X GET "http://localhost:5000/api/chat/memory/summary/user123" \
  -H "Authorization: Bearer <token>"

# Clear memory
curl -X DELETE "http://localhost:5000/api/chat/memory/user123" \
  -H "Authorization: Bearer <token>"
```

## Implementation Details

### Memory Service Integration

The MemoryService is integrated at the beginning of the RAG pipeline:

```python
def rag_pipeline(self, user_id, user_message, chat_history, input_type="text", content=None):
    # Step 1: Memory Processing
    memory_result = self.memory_service.process_conversation(user_id, memory_messages)
    
    # Step 2: Query Rephrasing
    rephrased_query = self.rephrase_query_with_context(user_message, chat_history)
    
    # Step 3: Enhanced RAG with memory context
    prompt = self._build_enhanced_prompt_with_memory(...)
    
    # Step 4: Store conversation in memory
    self.memory_service.process_conversation(user_id, full_conversation)
```

### Query Rephrasing

The query rephrasing follows the Haystack pattern:

```python
def rephrase_query_with_context(self, query, conversation_history):
    """Rephrase user query using conversation history for better retrieval."""
    prompt = f"""Rewrite the question for search while keeping its meaning and key terms intact.
    If the conversation history is empty, DO NOT change the query.
    Use conversation history only if necessary, and avoid extending the query with your own knowledge.
    If no changes are needed, output the current question as is.

    Conversation history:
    {conversation_context}

    User Query: {query}
    Rewritten Query:"""
```

## Benefits

### 1. Improved Conversation Continuity

- References previous conversations
- Maintains context across multiple interactions
- Handles follow-up questions effectively

### 2. Personalized Responses

- Uses user profile for customization
- Adapts to user preferences and style
- Provides more relevant and engaging responses

### 3. Better Information Retrieval

- Query rephrasing improves search accuracy
- Context-aware document retrieval
- Reduced irrelevant results

### 4. Memory Optimization

Following [Angular memory optimization practices](https://angulardive.com/blog/optimizing-your-angular-app-s-memory-usage/):
- Efficient memory storage and retrieval
- Automatic memory cleanup
- Scalable memory management

## Testing

Run the integration test:

```bash
cd flask_backend
python test_memory_integration.py
```

This will test:
- Memory service integration
- Query rephrasing
- User profile extraction
- Memory endpoints

## Configuration

The MemoryService uses LangGraph and LangChain components:

- **Memory Store**: InMemoryStore for user profiles
- **Conversation Memory**: ConversationBufferMemory for recent history
- **Summary Memory**: ConversationSummaryMemory for long-term context
- **Memory Graph**: StateGraph for conversation flow

## Future Enhancements

1. **Persistent Memory Storage**: Database-backed memory storage
2. **Memory Compression**: Automatic memory summarization
3. **Multi-modal Memory**: Support for image and audio memory
4. **Memory Analytics**: Usage patterns and optimization insights
5. **Memory Sharing**: Cross-user memory sharing capabilities

## References

- [Haystack Conversational RAG Documentation](https://haystack.deepset.ai/cookbook/conversational_rag_using_memory)
- [Angular Memory Optimization](https://angulardive.com/blog/optimizing-your-angular-app-s-memory-usage/)
- [Memory Leak Prevention](https://github.com/rakia/angular-memory-leaks) 