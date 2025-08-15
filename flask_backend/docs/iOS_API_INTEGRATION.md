# AI Assistant Flask Backend - iOS Integration Guide

## Overview
This document provides complete API documentation for iOS developers integrating with the AI Assistant Flask backend. The backend supports text chat, audio chat, image analysis, and multimodal interactions with a personalized AI assistant.

**Note:** All authentication endpoints now use standard REST API format with consistent response structure including `code`, `message`, `data`, and `timestamp` fields. This provides better error handling and follows [JSON API specification](https://jsonapi.org/examples/) best practices.

---

## Base URL & Configuration
```
Base URL: http://127.0.0.1:5050/
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN> (for protected endpoints)
```

---

## Authentication Endpoints

### 1. User Registration
**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "email": "string (optional)"
}
```

**Success Response (201):**
```json
{
  "code": 201,
  "message": "User registered successfully",
  "data": {
    "id": "string",
    "username": "string",
    "email": "string",
    "created_at": 1703123456,
    "is_active": true
  },
  "timestamp": 1703123456
}
```

**Validation Error Response (400):**
```json
{
  "code": 400,
  "message": "Validation failed",
  "errors": [
    {
      "status": "400",
      "source": {
        "pointer": "/data/attributes/username"
      },
      "title": "Validation Error",
      "detail": "Username is required"
    }
  ],
  "timestamp": 1703123456
}
```

**User Already Exists Response (409):**
```json
{
  "code": 409,
  "message": "Registration failed",
  "errors": [
    {
      "status": "409",
      "title": "User Already Exists",
      "detail": "Username already exists"
    }
  ],
  "timestamp": 1703123456
}
```

**Swift Example:**
```swift
let url = URL(string: "http://127.0.0.1:5050/api/auth/register")!
var request = URLRequest(url: url)
request.httpMethod = "POST"
request.setValue("application/json", forHTTPHeaderField: "Content-Type")

let body = [
    "username": "testuser",
    "password": "testpass123",
    "email": "user@example.com"
]
request.httpBody = try? JSONSerialization.data(withJSONObject: body)

URLSession.shared.dataTask(with: request) { data, response, error in
    if let data = data,
       let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
        
        if let httpResponse = response as? HTTPURLResponse {
            switch httpResponse.statusCode {
            case 201:
                // Success - extract user data
                if let userData = json["data"] as? [String: Any],
                   let username = userData["username"] as? String {
                    print("User registered: \(username)")
                }
            case 400:
                // Validation error
                if let errors = json["errors"] as? [[String: Any]] {
                    for error in errors {
                        if let detail = error["detail"] as? String {
                            print("Validation error: \(detail)")
                        }
                    }
                }
            case 409:
                // User already exists
                if let errors = json["errors"] as? [[String: Any]],
                   let detail = errors.first?["detail"] as? String {
                    print("Registration failed: \(detail)")
                }
            default:
                print("Unexpected status code: \(httpResponse.statusCode)")
            }
        }
    }
}.resume()
```

### 2. User Login
**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Success Response (200):**
```json
{
  "code": 200,
  "message": "Login successful",
  "data": {
    "type": "authentication",
    "attributes": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "user": {
        "id": "string",
        "username": "string",
        "email": "string",
        "created_at": "2025-01-15T10:30:00Z",
        "is_active": true
      },
      "created_at": 1703123456
    }
  },
  "timestamp": 1703123456
}
```

**Authentication Failed Response (401):**
```json
{
  "code": 401,
  "message": "Invalid credentials",
  "errors": [
    {
      "status": "401",
      "title": "Authentication Failed",
      "detail": "Invalid username or password"
    }
  ],
  "timestamp": 1703123456
}
```

**Swift Example:**
```swift
let url = URL(string: "http://127.0.0.1:5050/api/auth/login")!
var request = URLRequest(url: url)
request.httpMethod = "POST"
request.setValue("application/json", forHTTPHeaderField: "Content-Type")

let body = [
    "username": "testuser",
    "password": "testpass123"
]
request.httpBody = try? JSONSerialization.data(withJSONObject: body)

URLSession.shared.dataTask(with: request) { data, response, error in
    if let data = data,
       let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
        
        if let httpResponse = response as? HTTPURLResponse {
            switch httpResponse.statusCode {
            case 200:
                // Success - extract token and user data
                if let data = json["data"] as? [String: Any],
                   let attributes = data["attributes"] as? [String: Any],
                   let token = attributes["token"] as? String {
                    // Store token for future requests
                    UserDefaults.standard.set(token, forKey: "authToken")
                    
                    // Extract user info if needed
                    if let user = attributes["user"] as? [String: Any],
                       let username = user["username"] as? String {
                        print("Logged in as: \(username)")
                    }
                }
            case 401:
                // Authentication failed
                if let errors = json["errors"] as? [[String: Any]],
                   let detail = errors.first?["detail"] as? String {
                    print("Login failed: \(detail)")
                }
            default:
                print("Unexpected status code: \(httpResponse.statusCode)")
            }
        }
    }
}.resume()
```

### 3. Get User Profile
**Endpoint:** `GET /api/auth/profile`

**Headers:** `Authorization: Bearer <JWT_TOKEN>`

**Success Response (200):**
```json
{
  "code": 200,
  "message": "Profile retrieved successfully",
  "data": {
    "id": "string",
    "username": "string",
    "email": "string",
    "created_at": "2025-01-15T10:30:00Z",
    "is_active": true
  },
  "timestamp": 1703123456
}
```

**Unauthorized Response (401):**
```json
{
  "code": 401,
  "message": "Missing Authorization Header",
  "errors": [
    {
      "status": "401",
      "title": "Unauthorized",
      "detail": "Missing Authorization Header"
    }
  ],
  "timestamp": 1703123456
}
```

### 4. User Logout
**Endpoint:** `POST /api/auth/logout`

**Headers:** `Authorization: Bearer <JWT_TOKEN>`

**Success Response (200):**
```json
{
  "code": 200,
  "message": "Logout successful",
  "timestamp": 1703123456
}
```

---

## Chat Endpoints

### 1. Text Chat
**Endpoint:** `POST /api/chat/v1/text`

**Headers:** `Authorization: Bearer <JWT_TOKEN>`

**Request Body:**
```json
{
  "model": "im-chat",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you today?"
    }
  ],
  "max_tokens": 150,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "im-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I'm doing great! How about you?"
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

**Swift Example:**
```swift
let url = URL(string: "http://127.0.0.1:5050/api/chat/v1/text")!
var request = URLRequest(url: url)
request.httpMethod = "POST"
request.setValue("application/json", forHTTPHeaderField: "Content-Type")
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

let body = [
    "model": "im-chat",
    "messages": [
        ["role": "user", "content": "Hello, how are you today?"]
    ],
    "max_tokens": 150,
    "temperature": 0.7
]
request.httpBody = try? JSONSerialization.data(withJSONObject: body)
```

### 2. Audio Chat
**Endpoint:** `POST /api/chat/v1/audio`

**Headers:** `Authorization: Bearer <JWT_TOKEN>`

**Request Body:**
```json
{
  "model": "im-chat",
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
  ]
}
```

**Response:**
- **Audio Response:** Returns audio file (MPEG) with transcription in header
- **Text Response:** JSON in OpenAI format

**Swift Example (Audio Recording):**
```swift
// Convert audio to base64
let audioData = // ... your recorded audio data
let base64String = audioData.base64EncodedString()

let body = [
    "model": "im-chat",
    "messages": [
        [
            "role": "user",
            "content": [
                ["type": "text", "text": "Optional text message"],
                [
                    "type": "audio_url",
                    "audio_url": ["url": "data:audio/wav;base64,\(base64String)"]
                ]
            ]
        ]
    ]
]
```

### 3. Mobile Unified Chat (Recommended for iOS)
**Endpoint:** `POST /api/chat/v1/mobile`

**Headers:** `Authorization: Bearer <JWT_TOKEN>`

This endpoint automatically handles text, image, and audio inputs and returns appropriate responses including audio synthesis.

**Request Body (Text):**
```json
{
  "model": "im-chat",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ]
}
```

**Request Body (Image):**
```json
{
  "model": "im-chat",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What do you see in this image?"
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

**Request Body (Audio):**
```json
{
  "model": "im-chat",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "audio_url",
          "audio_url": {
            "url": "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT..."
          }
        }
      ]
    }
  ]
}
```

**Response (Text/Image):**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "im-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I can see a beautiful sunset over the mountains in this image."
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

**Response (Audio - includes synthesized audio):**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "im-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": [
          {
            "type": "text",
            "text": "I understand your audio message. Here's my response."
          },
          {
            "type": "audio_url",
            "audio_url": {
              "url": "data:audio/mpeg;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT..."
            }
          }
        ]
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

---

## Health Check
**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok"
}
```

---

## Response Format

The API follows standard REST API format with consistent response structure:

### Success Response Format
```json
{
  "code": 200,
  "message": "Success message",
  "data": {
    // Response data
  },
  "timestamp": 1703123456
}
```

### Error Response Format
```json
{
  "code": 400,
  "message": "Error message",
  "errors": [
    {
      "status": "400",
      "source": {
        "pointer": "/data/attributes/field"
      },
      "title": "Error Title",
      "detail": "Detailed error message"
    }
  ],
  "timestamp": 1703123456
}
```

## Error Handling

All endpoints return standard HTTP status codes and JSON error responses following the REST API format:

**Common Status Codes:**
- `200` - Success
- `201` - Created (for registration)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid or missing JWT token)
- `404` - Not Found
- `409` - Conflict (user already exists)
- `500` - Internal Server Error

**Swift Error Handling Example:**
```swift
URLSession.shared.dataTask(with: request) { data, response, error in
    if let httpResponse = response as? HTTPURLResponse {
        switch httpResponse.statusCode {
        case 200...299:
            // Success - handle data
            if let data = data,
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                // Parse success response
                if let message = json["message"] as? String {
                    print("Success: \(message)")
                }
            }
        case 401:
            // Unauthorized - redirect to login
            DispatchQueue.main.async {
                // Show login screen
            }
        case 400, 409:
            // Bad request or conflict - show error message
            if let data = data,
               let errorJson = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let errors = errorJson["errors"] as? [[String: Any]] {
                
                var errorMessages: [String] = []
                for error in errors {
                    if let detail = error["detail"] as? String {
                        errorMessages.append(detail)
                    }
                }
                
                DispatchQueue.main.async {
                    // Show errors: errorMessages.joined(separator: ", ")
                }
            }
        default:
            // Handle other errors
            if let data = data,
               let errorJson = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let message = errorJson["message"] as? String {
                DispatchQueue.main.async {
                    // Show error: message
                }
            }
        }
    }
}.resume()
```

---

## iOS Integration Best Practices

### 1. Token Management
```swift
class AuthManager {
    static let shared = AuthManager()
    
    var authToken: String? {
        get { UserDefaults.standard.string(forKey: "authToken") }
        set { UserDefaults.standard.set(newValue, forKey: "authToken") }
    }
    
    func addAuthHeader(to request: inout URLRequest) {
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
    }
}
```

### 2. API Client
```swift
class APIClient {
    static let shared = APIClient()
    private let baseURL = "http://127.0.0.1:5050"
    
    func sendRequest<T: Codable>(endpoint: String, method: String = "GET", body: [String: Any]? = nil, responseType: T.Type) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        AuthManager.shared.addAuthHeader(to: &request)
        
        if let body = body {
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        }
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode == 401 {
            // Handle unauthorized - redirect to login
            throw APIError.unauthorized
        }
        
        if httpResponse.statusCode != 200 {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try JSONDecoder().decode(responseType, from: data)
    }
}
```

### 3. Chat Service
```swift
class ChatService {
    static let shared = ChatService()
    
    func sendTextMessage(_ message: String) async throws -> ChatResponse {
        let body = [
            "model": "im-chat",
            "messages": [
                ["role": "user", "content": message]
            ]
        ]
        
        return try await APIClient.shared.sendRequest(
            endpoint: "/api/chat/v1/mobile",
            method: "POST",
            body: body,
            responseType: ChatResponse.self
        )
    }
    
    func sendAudioMessage(audioData: Data, textMessage: String? = nil) async throws -> ChatResponse {
        let base64String = audioData.base64EncodedString()
        
        var content: [[String: Any]] = []
        
        if let text = textMessage {
            content.append(["type": "text", "text": text])
        }
        
        content.append([
            "type": "audio_url",
            "audio_url": ["url": "data:audio/wav;base64,\(base64String)"]
        ])
        
        let body = [
            "model": "im-chat",
            "messages": [
                ["role": "user", "content": content]
            ]
        ]
        
        return try await APIClient.shared.sendRequest(
            endpoint: "/api/chat/v1/mobile",
            method: "POST",
            body: body,
            responseType: ChatResponse.self
        )
    }
}
```

---

## Voice Profiles

The backend supports different voice profiles for audio responses:
- `魅力女友` (Charming Girlfriend) - uses "nova" voice
- `柔美女友` (Gentle Girlfriend) - uses "shimmer" voice  
- `傲娇霸总` (Tsundere Boss) - uses "onyx" voice
- `正直青年` (Upright Youth) - uses "echo" voice

Voice selection is handled automatically based on the user's conversation history and preferences.

---

## Important Notes

1. **Authentication**: All chat endpoints require a valid JWT token in the Authorization header
2. **Media Format**: Images and audio should be sent as base64-encoded strings in the JSON payload
3. **Response Format**: Follows OpenAI API format for compatibility
4. **Audio Synthesis**: The mobile endpoint automatically synthesizes audio responses when appropriate
5. **Session Memory**: The backend maintains conversation context and user preferences automatically
6. **Error Handling**: Always check HTTP status codes and handle errors gracefully
7. **Token Expiration**: JWT tokens expire after 1 hour - implement refresh logic if needed

---

## Testing

You can test the endpoints using curl or Postman:

```bash
# Register new user
curl -X POST http://127.0.0.1:5050/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123", "email": "test@example.com"}'

# Login
curl -X POST http://127.0.0.1:5050/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Get user profile
curl -X GET http://127.0.0.1:5050/api/auth/profile \
  -H "Authorization: Bearer YOUR_TOKEN"

# Send text message
curl -X POST http://127.0.0.1:5050/api/chat/v1/mobile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"model": "im-chat", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Expected Response Examples

**Successful Registration:**
```json
{
  "code": 201,
  "message": "User registered successfully",
  "data": {
    "id": "testuser",
    "username": "testuser",
    "email": "test@example.com",
    "created_at": 1703123456,
    "is_active": true
  },
  "timestamp": 1703123456
}
```

**Successful Login:**
```json
{
  "code": 200,
  "message": "Login successful",
  "data": {
    "type": "authentication",
    "attributes": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "user": {
        "id": "testuser",
        "username": "testuser",
        "email": "test@example.com",
        "created_at": "2025-01-15T10:30:00Z",
        "is_active": true
      },
      "created_at": 1703123456
    }
  },
  "timestamp": 1703123456
}
``` 