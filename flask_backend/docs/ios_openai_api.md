# IM-AI Mobile API

A single HTTPS endpoint gives your iOS (Swift) app chat access with text, image _and/or_ audio in **OpenAI-compatible format**.

```
POST /api/chat/v1/mobile  (JSON)
Authorization: Bearer <jwt or "no-auth-tests">
Content-Type: application/json
```

Request body
------------
```jsonc
{
  "model": "im-chat",        // optional, always "im-chat" for now
  "messages": [               // array exactly like OpenAI Chat API
    { "role": "user", "content": "Hello" },

    // multimodal example (text + image + audio in ONE message)
    {
      "role": "user",
      "content": [
        { "type": "text", "text": "Describe this image and answer aloud" },
        { "type": "image_url",  "image_url": { "url": "data:image/jpeg;base64,<...>" } },
        { "type": "audio_url",  "audio_url": { "url": "data:audio/wav;base64,<...>" } }
      ]
    }
  ]
}
```

Response body
-------------
```jsonc
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "im-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hi there! …"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": { /* tokens */ }
}
```

If the **request contained audio** the assistant _also_ returns speech:
```jsonc
"content": [
  { "type": "text",      "text": "Here’s the answer" },
  { "type": "audio_url", "audio_url": { "url": "data:audio/mpeg;base64,<mp3>" } }
]
```

Swift example
-------------
```swift
struct ChatMessage: Codable {
    let role: String
    let content: CodableValue // see below
}

// Tiny helper that can encode either String or [OpenAIContentItem]
struct CodableValue: Codable {
    let value: Any
    init(_ v: Any) { value = v }
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let s = value as? String { try container.encode(s) }
        else if let a = value as? [OpenAIContentItem] { try container.encode(a) }
    }
}

struct OpenAIContentItem: Codable {
    let type: String
    let text: String?       // when type == "text"
    let image_url: URLBox?  // when type == "image_url"
    let audio_url: URLBox?  // when type == "audio_url"
}

struct URLBox: Codable { let url: String }

let token = "no-auth-tests" // or JWT after login
var request = URLRequest(url: URL(string: "https://api.example.com/api/chat/v1/mobile")!)
request.httpMethod = "POST"
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
request.setValue("application/json", forHTTPHeaderField: "Content-Type")

let messages: [ChatMessage] = [
    ChatMessage(role: "user", content: CodableValue("How are you?"))
]

request.httpBody = try JSONEncoder().encode(["model": "im-chat", "messages": messages])

URLSession.shared.dataTask(with: request) { data, _, _ in
    // parse OpenAI response
}.resume()
```

Status codes
------------
| Code | Meaning |
|------|---------|
| 200  | Success |
| 400  | Bad request (missing message) |
| 401  | Auth required / invalid token |
| 500  | Internal error |

Notes
-----
* Send **base64** media _without_ the `data:` prefix in the JSON field; the server adds it if missing.
* Maximum payload size is 4 MB.
* Streaming is not yet supported; use polling or WebSocket (future work). 