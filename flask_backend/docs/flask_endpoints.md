# AI Assistant Flask Backend – iOS Mobile Integration Guide

## Overview
This document provides all the information an iOS mobile app developer needs to integrate with the Flask backend for the AI Assistant project. It covers authentication, main API endpoints, request/response formats, media handling, and important notes for a smooth integration.

---

## Base URL
```
http://127.0.0.1:5050/
```

---

## Authentication
All protected endpoints require a JWT token in the `Authorization` header.

### Register
- **POST** `/api/auth/register`
- **Body:**
```json
{
  "username": "string",
  "password": "string",
  "email": "string (optional)"
}
```
- **Response:**
```json
{
  "message": "User registered successfully",
  "username": "string"
}
```

### Login
- **POST** `/api/auth/login`
- **Body:**
```json
{
  "username": "string",
  "password": "string"
}
```
- **Response:**
```json
{
  "token": "<JWT_TOKEN>",
  "username": "string",
  "message": "Login successful"
}
```

### Get Profile
- **GET** `/api/auth/profile`
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Response:**
```json
{
  "username": "string",
  "email": "string",
  "created_at": "datetime",
  "is_active": true
}
```

### Logout
- **POST** `/api/auth/logout`
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Response:**
```json
{
  "message": "Logout successful"
}
```

---

## Main API Endpoints

### Text Chat
- **POST** `/api/chat/v1/text`
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Body:**
```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "What's the weather like today?"
    },
    {
      "role": "assistant", 
      "content": "It's sunny and warm."
    },
    {
      "role": "user",
      "content": "What about tomorrow?"
    }
  ],
  "max_tokens": 150,
  "temperature": 0.7
}
```
- **Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Tomorrow will be partly cloudy with a high of 22°C."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 56,
    "completion_tokens": 12,
    "total_tokens": 68
  }
}
```

#### About the `messages` Field
The `messages` field follows the OpenAI API format with an array of message objects. Each message has a `role` ("system", "user", or "assistant") and `content` (text or multimodal content).

**Example: Sending an image in a text chat**
```json
{
  "model": "gpt-4-vision-preview",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What is in this picture?"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD..."
          }
        }
      ]
    }
  ]
}
```

**Example: Sending plain text (no image)**
```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "user",
      "content": "Tell me a joke."
    }
  ]
}
```

### Audio Chat
- **POST** `/api/chat/v1/audio`
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Body:**
```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Optional text message"
        },
        {
          "type": "audio_url",
          "audio_url": {
            "url": "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT..."
          }
        }
      ]
    }
  ],
  "max_tokens": 150,
  "temperature": 0.7
}
```
- **Response:**
  - **Audio Response:** Returns audio file (MPEG) with transcription in header
  - **Text Response:** JSON in OpenAI format:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I understand your audio message. Here's my response."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 15,
    "total_tokens": 60
  }
}
```

#### About Audio Input
The audio input follows OpenAI's multimodal format with `audio_url` containing a data URL. The audio is automatically transcribed and processed through the chat pipeline.

### File Upload
- **POST** `/api/chat/upload-file`
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Form Data:** `file` (binary)
- **Response:**
```json
{
  "file_id": "string"
}
```

---

## Mobile-Specific Endpoints

### Mobile Chat
- **POST** `/api/mobile/v1/chat`
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Body:**
```json
{
  "model": "im-chat",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What is in this image?"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD..."
          }
        }
      ]
    }
  ]
}
```
- **Response:**
  - For audio: returns audio file or `{ "audio_base64": "string" }`
  - For text/image: OpenAI format response
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "This image shows a beautiful sunset over the mountains."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 15,
    "total_tokens": 60
  }
}
```

### Session Memory
- **GET** `/api/mobile/v1/session-memory`
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Response:**
```json
{
  "extracted_info": [ ... ]
}
```

---

## Media Handling
- **Audio/Image Upload:** Send as base64-encoded string in JSON (`content` field).
- **Audio Response:** May be returned as a file (MPEG) or as a base64 string in JSON.
- **File Upload:** Use multipart/form-data for binary files.

---

## Error Handling
- **Error responses** are always JSON:
```json
{
  "error": "Error message"
}
```

---

## Differences from Previous Java Backend
- **Endpoint paths and request/response formats may have changed.**
- **Authentication now uses JWT tokens.**
- **Media is handled as base64 in JSON, not as multipart unless uploading files.**
- **User table and logic may differ (see Java SQL schema for reference).**

---

## Example Usage

### Login Example (Swift)
```swift
let url = URL(string: "http://<server>/api/auth/login")!
var request = URLRequest(url: url)
request.httpMethod = "POST"
request.setValue("application/json", forHTTPHeaderField: "Content-Type")
let body = ["username": "testuser", "password": "testpass"]
request.httpBody = try? JSONSerialization.data(withJSONObject: body)
// ... send request and handle response
``` 