# AI Assistant Mobile API – Flask vs Java Backend Comparison

## Overview
This document compares the iOS mobile integration points for the Flask and Java (Spring Boot) backends of the AI Assistant project. It highlights similarities, differences, and migration notes for developers.

---

## Base URL
| Backend | Base URL Example                  |
|---------|-----------------------------------|
| Flask   | http://127.0.0.1:5050/           |
| Java    | http://<server>:8081/            |

---

## Authentication
| Feature         | Flask Backend                                 | Java Backend                                 |
|-----------------|-----------------------------------------------|----------------------------------------------|
| Register        | POST /api/auth/register                       | POST /api/auth/register                      |
| Login           | POST /api/auth/login                          | POST /api/auth/login                         |
| Token           | JWT in Authorization header                   | JWT in Authorization header                  |
| Profile         | GET /api/auth/profile                         | (Returned in login response as 'user')       |
| Logout          | POST /api/auth/logout                         | (Not explicit, client removes token)         |

---

## Main Endpoints
| Feature/Entity      | Flask Backend                        | Java Backend                                 |
|---------------------|--------------------------------------|----------------------------------------------|
| Text Chat           | POST /api/chat/v1/text               | (Not present, handled via assistants)        |
| Audio Chat          | POST /api/chat/v1/audio              | (Not present, handled via voice profiles)    |
| File Upload         | POST /api/chat/upload-file           | (Handled via voice/file endpoints)           |
| Mobile Chat         | POST /api/mobile/v1/chat             | (Not present)                               |
| Session Memory      | GET /api/mobile/v1/session-memory    | (Not present)                               |
| AI Assistant CRUD   | (Not present)                        | /api/assistants (CRUD)                      |
| Voice List          | (Not present)                        | GET /api/assistants/voice-list              |
| Voice Profile CRUD  | (Not present)                        | /api/voice-profiles (CRUD, by id/audio/file)|

---

## Media Handling
| Aspect         | Flask Backend                                 | Java Backend                                 |
|---------------|-----------------------------------------------|----------------------------------------------|
| Audio/Image   | Base64 in JSON (content field)                | Managed via voice profile endpoints          |
| File Upload   | multipart/form-data (upload-file endpoint)     | Binary/file endpoints, referenced by ID      |
| Audio Reply   | Audio file (MPEG) or base64 in JSON           | Voice profile endpoints, file download       |

---

## Error Handling
| Aspect         | Flask Backend                                 | Java Backend                                 |
|---------------|-----------------------------------------------|----------------------------------------------|
| Format        | JSON: { "error": "message" }                 | JSON or standard HTTP error codes            |

---

## Notable Differences
- **Flask backend** focuses on chat (text/audio), session memory, and direct media upload for mobile clients.
- **Java backend** focuses on AI assistant and voice profile management, with more structured CRUD endpoints.
- **Media handling**: Flask uses base64 in JSON for audio/image, Java uses file/profile endpoints.
- **Authentication**: Both use JWT, but profile info is accessed differently.
- **Endpoint structure**: Flask is chat-centric, Java is entity-centric (assistants, profiles).

---

## Migration Notes
- When migrating from Java to Flask, update endpoint paths, request/response formats, and media handling logic in the mobile app.
- JWT authentication remains similar, but user profile and assistant management differ.

---

## See Also
- [Flask API Integration Guide](./API_MOBILE_INTEGRATION.md)
- [Java API Integration Guide](./API_MOBILE_INTEGRATION_JAVA.md) 