# Upload Endpoints API Documentation
# 上传端点 API 文档

This document provides comprehensive documentation for all upload-related endpoints in the IM Chat backend API.

本文档提供了 IM Chat 后端 API 中所有上传相关端点的完整文档。

## Base URL
## 基础 URL
```
http://localhost:5050/api/chat/upload
```

## Authentication
## 身份验证

All endpoints require JWT authentication via the Authorization header:

所有端点都需要通过 Authorization 头部进行 JWT 身份验证：
```
Authorization: Bearer <your_jwt_token>
```

## Standardized Response Format
## 标准化响应格式

All endpoints follow a consistent response format:

所有端点都遵循一致的响应格式：

### Success Response
### 成功响应
```json
{
  "code": 200,
  "message": "Operation completed successfully",
  "success": true,
  "data": {
    // Response data here
  }
}
```

### Error Response
### 错误响应
```json
{
  "code": 400,
  "message": "Error description",
  "success": false
}
```

---

## 1. Upload Image / 上传图片

**Endpoint:** `POST /api/chat/upload/image`

**Description:** Upload image files (PNG, JPG, JPEG, GIF, BMP, WebP)
**描述:** 上传图片文件 (PNG, JPG, JPEG, GIF, BMP, WebP)

### Request Format / 请求格式

#### Headers / 请求头
```
Authorization: Bearer <your_jwt_token>
Content-Type: multipart/form-data
```

#### Form Data / 表单数据
| Parameter / 参数 | Type / 类型 | Required / 必需 | Description / 描述 |
|------------------|-------------|-----------------|-------------------|
| `file` | file | Yes / 是 | Image file to upload / 要上传的图片文件 |

#### Supported Formats / 支持的格式
- PNG, JPG, JPEG, GIF, BMP, WebP

### Response Format / 响应格式

#### Success Response (200 OK) / 成功响应 (200 OK)
```json
{
  "code": 200,
  "message": "Image uploaded successfully",
  "success": true,
  "data": {
    "s3_url": "https://im-chat-bucket.s3.amazonaws.com/chat-images/image-1755195674.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAYLZYO4GGIQOAWC2O%2F20250814%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250814T182114Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host&X-Amz-Signature=558906d421a6edb82b52427d62117d6aeea1fff7bfa9b29e075bf008d9fcfcb5",
    "s3_key": "chat-images/image-1755195674.jpg",
    "bucket": "im-chat-bucket",
    "filename": "image.jpg"
  }
}
```

#### Error Response (400 Bad Request) / 错误响应 (400 Bad Request)
```json
{
  "code": 400,
  "message": "No file provided",
  "success": false
}
```

```json
{
  "code": 400,
  "message": "Invalid file type. Allowed: png, jpg, jpeg, gif, bmp, webp",
  "success": false
}
```

---

## 2. Upload Audio / 上传音频

**Endpoint:** `POST /api/chat/upload/audio`

**Description:** Upload audio files (WAV, MP3, M4A, AAC, OGG, FLAC)
**描述:** 上传音频文件 (WAV, MP3, M4A, AAC, OGG, FLAC)

### Request Format / 请求格式

#### Headers / 请求头
```
Authorization: Bearer <your_jwt_token>
Content-Type: multipart/form-data
```

#### Form Data / 表单数据
| Parameter / 参数 | Type / 类型 | Required / 必需 | Description / 描述 |
|------------------|-------------|-----------------|-------------------|
| `file` | file | Yes / 是 | Audio file to upload / 要上传的音频文件 |

#### Supported Formats / 支持的格式
- WAV, MP3, M4A, AAC, OGG, FLAC

### Response Format / 响应格式

#### Success Response (200 OK) / 成功响应 (200 OK)
```json
{
  "code": 200,
  "message": "Audio uploaded successfully",
  "success": true,
  "data": {
    "s3_url": "https://im-chat-bucket.s3.amazonaws.com/chat-audio/audio-1755195675.wav?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAYLZYO4GGIQOAWC2O%2F20250814%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250814T182115Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host&X-Amz-Signature=69da63fde561bbd84e997080db01550553d52df139470941d72275f8b049938b",
    "s3_key": "chat-audio/audio-1755195675.wav",
    "bucket": "im-chat-bucket",
    "filename": "audio.wav"
  }
}
```

#### Error Response (400 Bad Request) / 错误响应 (400 Bad Request)
```json
{
  "code": 400,
  "message": "No file provided",
  "success": false
}
```

```json
{
  "code": 400,
  "message": "Invalid file type. Allowed: wav, mp3, m4a, aac, ogg, flac",
  "success": false
}
```

---

## 3. Upload Any File / 上传任意文件

**Endpoint:** `POST /api/chat/upload/file`

**Description:** Upload any file type (auto-detects image/audio)
**描述:** 上传任意文件类型 (自动检测图片/音频)

### Request Format / 请求格式

#### Headers / 请求头
```
Authorization: Bearer <your_jwt_token>
Content-Type: multipart/form-data
```

#### Form Data / 表单数据
| Parameter / 参数 | Type / 类型 | Required / 必需 | Description / 描述 |
|------------------|-------------|-----------------|-------------------|
| `file` | file | Yes / 是 | File to upload / 要上传的文件 |

### Response Format / 响应格式

#### Success Response (200 OK) / 成功响应 (200 OK)
```json
{
  "code": 200,
  "message": "File uploaded successfully",
  "success": true,
  "data": {
    "s3_url": "https://im-chat-bucket.s3.amazonaws.com/chat-files/document-1755195676.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAYLZYO4GGIQOAWC2O%2F20250814%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250814T182116Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host&X-Amz-Signature=7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0",
    "s3_key": "chat-files/document-1755195676.pdf",
    "bucket": "im-chat-bucket",
    "filename": "document.pdf",
    "file_type": "images"
  }
}
```

#### Error Response (400 Bad Request) / 错误响应 (400 Bad Request)
```json
{
  "code": 400,
  "message": "No file provided",
  "success": false
}
```

```json
{
  "code": 400,
  "message": "Invalid file type",
  "success": false
}
```

---

## 4. List All Files / 列出所有文件

**Endpoint:** `GET /api/chat/upload/files`

**Description:** List all files in the system
**描述:** 列出系统中的所有文件

### Request Format / 请求格式

#### Headers / 请求头
```
Authorization: Bearer <your_jwt_token>
```

### Response Format / 响应格式

#### Success Response (200 OK) / 成功响应 (200 OK)
```json
{
  "code": 200,
  "message": "Files retrieved successfully",
  "success": true,
  "data": {
    "files": [
      {
        "key": "chat-images/image-1755195674.jpg",
        "size": 1024000,
        "last_modified": "2025-08-14T18:21:14.000Z",
        "url": "https://im-chat-bucket.s3.amazonaws.com/chat-images/image-1755195674.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAYLZYO4GGIQOAWC2O%2F20250814%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250814T182114Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=558906d421a6edb82b52427d62117d6aeea1fff7bfa9b29e075bf008d9fcfcb5"
      }
    ],
    "total_count": 38
  }
}
```

#### Error Response (401 Unauthorized) / 错误响应 (401 Unauthorized)
```json
{
  "code": 401,
  "message": "Authentication required",
  "success": false
}
```

---

## 5. List User Files / 列出用户文件

**Endpoint:** `GET /api/chat/upload/files/user/<user_id>`

**Description:** List files for a specific user
**描述:** 列出特定用户的文件

### Request Format / 请求格式

#### Headers / 请求头
```
Authorization: Bearer <your_jwt_token>
```

#### Path Parameters / 路径参数
| Parameter / 参数 | Type / 类型 | Required / 必需 | Description / 描述 |
|------------------|-------------|-----------------|-------------------|
| `user_id` | string | Yes / 是 | The user ID to list files for / 要列出文件的用户ID |

### Response Format / 响应格式

#### Success Response (200 OK) / 成功响应 (200 OK)
```json
{
  "code": 200,
  "message": "User files retrieved successfully",
  "success": true,
  "data": {
    "files": [
      {
        "key": "chat-images/image-1755195674.jpg",
        "size": 1024000,
        "last_modified": "2025-08-14T18:21:14.000Z",
        "file_type": "image",
        "filename": "image-1755195674.jpg",
        "url": "https://im-chat-bucket.s3.amazonaws.com/chat-images/image-1755195674.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAYLZYO4GGIQOAWC2O%2F20250814%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250814T182114Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=558906d421a6edb82b52427d62117d6aeea1fff7bfa9b29e075bf008d9fcfcb5"
      }
    ],
    "total_count": 38,
    "requested_user_id": "user_8s7yfq",
    "current_user_id": "user_8s7yfq"
  }
}
```

#### Error Response (401 Unauthorized) / 错误响应 (401 Unauthorized)
```json
{
  "code": 401,
  "message": "Authentication required",
  "success": false
}
```

#### Error Response (404 Not Found) / 错误响应 (404 Not Found)
```json
{
  "code": 404,
  "message": "User not found",
  "success": false
}
```

---

## Examples / 示例

### cURL Examples / cURL 示例

#### Upload Image / 上传图片
```bash
curl -X POST "http://localhost:5050/api/chat/upload/image" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -F "file=@/path/to/image.jpg"
```

#### Upload Audio / 上传音频
```bash
curl -X POST "http://localhost:5050/api/chat/upload/audio" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -F "file=@/path/to/audio.wav"
```

#### Upload Any File / 上传任意文件
```bash
curl -X POST "http://localhost:5050/api/chat/upload/file" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -F "file=@/path/to/document.pdf"
```

#### List All Files / 列出所有文件
```bash
curl -X GET "http://localhost:5050/api/chat/upload/files" \
  -H "Authorization: Bearer <your_jwt_token>"
```

#### List User Files / 列出用户文件
```bash
curl -X GET "http://localhost:5050/api/chat/upload/files/user/user_8s7yfq" \
  -H "Authorization: Bearer <your_jwt_token>"
```

### iOS Swift Examples / iOS Swift 示例

#### Data Models / 数据模型
```swift
import Foundation

// MARK: - Response Models / 响应模型
struct ImageUploadResponse: Codable {
    let code: Int
    let message: String
    let success: Bool
    let data: ImageUploadData
}

struct ImageUploadData: Codable {
    let s3Url: String
    let s3Key: String
    let bucket: String
    let filename: String
    
    enum CodingKeys: String, CodingKey {
        case s3Url = "s3_url"
        case s3Key = "s3_key"
        case bucket, filename
    }
}

struct AudioUploadResponse: Codable {
    let code: Int
    let message: String
    let success: Bool
    let data: AudioUploadData
}

struct AudioUploadData: Codable {
    let s3Url: String
    let s3Key: String
    let bucket: String
    let filename: String
    
    enum CodingKeys: String, CodingKey {
        case s3Url = "s3_url"
        case s3Key = "s3_key"
        case bucket, filename
    }
}

struct FileUploadResponse: Codable {
    let code: Int
    let message: String
    let success: Bool
    let data: FileUploadData
}

struct FileUploadData: Codable {
    let s3Url: String
    let s3Key: String
    let bucket: String
    let filename: String
    let fileType: String
    
    enum CodingKeys: String, CodingKey {
        case s3Url = "s3_url"
        case s3Key = "s3_key"
        case bucket, filename
        case fileType = "file_type"
    }
}

struct FileListResponse: Codable {
    let code: Int
    let message: String
    let success: Bool
    let data: FileListData
}

struct FileListData: Codable {
    let files: [FileInfo]
    let totalCount: Int
    
    enum CodingKeys: String, CodingKey {
        case files
        case totalCount = "total_count"
    }
}

struct FileInfo: Codable {
    let key: String
    let size: Int
    let lastModified: String
    let url: String
    
    enum CodingKeys: String, CodingKey {
        case key, size, url
        case lastModified = "last_modified"
    }
}

struct UserFileListResponse: Codable {
    let code: Int
    let message: String
    let success: Bool
    let data: UserFileListData
}

struct UserFileListData: Codable {
    let files: [UserFileInfo]
    let totalCount: Int
    let requestedUserId: String
    let currentUserId: String
    
    enum CodingKeys: String, CodingKey {
        case files
        case totalCount = "total_count"
        case requestedUserId = "requested_user_id"
        case currentUserId = "current_user_id"
    }
}

struct UserFileInfo: Codable {
    let key: String
    let size: Int
    let lastModified: String
    let fileType: String
    let filename: String
    let url: String
    
    enum CodingKeys: String, CodingKey {
        case key, size, filename, url
        case lastModified = "last_modified"
        case fileType = "file_type"
    }
}

struct ErrorResponse: Codable {
    let code: Int
    let message: String
    let success: Bool
}

enum UploadError: Error {
    case invalidResponse
    case apiError(String)
    case invalidImageData
}

enum FileError: Error {
    case invalidResponse
    case apiError(String)
}
```

#### Upload Service / 上传服务
```swift
import Foundation
import UIKit

class UploadService {
    private let baseURL = "http://localhost:5050/api/chat/upload"
    private let token: String
    
    init(token: String) {
        self.token = token
    }
    
    // MARK: - Upload Methods / 上传方法
    
    func uploadImage(_ image: UIImage, filename: String = "image.jpg") async throws -> ImageUploadResponse {
        guard let imageData = image.jpegData(compressionQuality: 0.8) else {
            throw UploadError.invalidImageData
        }
        
        return try await uploadFile(
            fileData: imageData,
            filename: filename,
            endpoint: "/image"
        )
    }
    
    func uploadAudio(audioData: Data, filename: String) async throws -> AudioUploadResponse {
        return try await uploadFile(
            fileData: audioData,
            filename: filename,
            endpoint: "/audio"
        )
    }
    
    func uploadAnyFile(fileData: Data, filename: String) async throws -> FileUploadResponse {
        return try await uploadFile(
            fileData: fileData,
            filename: filename,
            endpoint: "/file"
        )
    }
    
    private func uploadFile<T: Codable>(fileData: Data, filename: String, endpoint: String) async throws -> T {
        let url = URL(string: "\(baseURL)\(endpoint)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw UploadError.invalidResponse
        }
        
        if httpResponse.statusCode == 200 {
            return try JSONDecoder().decode(T.self, from: data)
        } else {
            let errorResponse = try JSONDecoder().decode(ErrorResponse.self, from: data)
            throw UploadError.apiError(errorResponse.message ?? "Upload failed")
        }
    }
    
    // MARK: - File Management Methods / 文件管理方法
    
    func getAllFiles() async throws -> FileListResponse {
        let url = URL(string: "\(baseURL)/files")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw FileError.invalidResponse
        }
        
        if httpResponse.statusCode == 200 {
            return try JSONDecoder().decode(FileListResponse.self, from: data)
        } else {
            let errorResponse = try JSONDecoder().decode(ErrorResponse.self, from: data)
            throw FileError.apiError(errorResponse.message ?? "Failed to load files")
        }
    }
    
    func getUserFiles(userId: String) async throws -> UserFileListResponse {
        let url = URL(string: "\(baseURL)/files/user/\(userId)")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw FileError.invalidResponse
        }
        
        if httpResponse.statusCode == 200 {
            return try JSONDecoder().decode(UserFileListResponse.self, from: data)
        } else {
            let errorResponse = try JSONDecoder().decode(ErrorResponse.self, from: data)
            throw FileError.apiError(errorResponse.message ?? "Failed to load user files")
        }
    }
}
```

#### Usage Example / 使用示例
```swift
import UIKit

class UploadViewController: UIViewController {
    @IBOutlet weak var imageView: UIImageView!
    @IBOutlet weak var uploadButton: UIButton!
    @IBOutlet weak var statusLabel: UILabel!
    
    private let uploadService = UploadService(token: "your_jwt_token")
    
    @IBAction func uploadButtonTapped(_ sender: UIButton) {
        guard let image = imageView.image else {
            showError("No image to upload / 没有图片可上传")
            return
        }
        
        Task {
            do {
                showStatus("Uploading image... / 正在上传图片...")
                let response = try await uploadService.uploadImage(image)
                
                DispatchQueue.main.async {
                    self.showSuccess("Image uploaded successfully! / 图片上传成功！")
                    print("S3 URL: \(response.data.s3Url)")
                    print("Message: \(response.message)")
                }
            } catch {
                DispatchQueue.main.async {
                    self.showError("Upload failed: \(error) / 上传失败: \(error)")
                }
            }
        }
    }
    
    private func showStatus(_ message: String) {
        DispatchQueue.main.async {
            self.statusLabel.text = message
            self.statusLabel.textColor = .blue
        }
    }
    
    private func showSuccess(_ message: String) {
        DispatchQueue.main.async {
            self.statusLabel.text = message
            self.statusLabel.textColor = .green
        }
    }
    
    private func showError(_ message: String) {
        DispatchQueue.main.async {
            self.statusLabel.text = message
            self.statusLabel.textColor = .red
        }
    }
}
```

---

## Error Handling / 错误处理

### HTTP Status Codes / HTTP 状态码
- **200 OK:** Successful operation / 操作成功
- **400 Bad Request:** Invalid file type, missing file, or invalid parameters / 无效的文件类型、缺少文件或无效参数
- **401 Unauthorized:** Missing or invalid JWT token / 缺少或无效的 JWT 令牌
- **404 Not Found:** User not found / 用户未找到
- **500 Internal Server Error:** Server-side error / 服务器端错误

### Common Error Scenarios / 常见错误场景
1. **No file provided:** User didn't select a file / 用户未选择文件
2. **Invalid file type:** File extension not supported / 不支持的文件扩展名
3. **Authentication failed:** JWT token expired or invalid / JWT 令牌过期或无效
4. **Upload failed:** Network or server error / 网络或服务器错误

## URL Expiry / URL 过期时间

- **Upload Response URLs:** 24 hours (86400 seconds) / 上传响应 URL：24 小时 (86400 秒)
- **File List URLs:** 1 hour (3600 seconds) / 文件列表 URL：1 小时 (3600 秒)

Applications should refresh file lists if URLs are needed for longer periods.

