# REST API 认证端点文档

## 基础 URL

```
http://localhost:5050/api/auth
```

## 认证端点

### 1. 用户注册

**端点:** `POST /api/auth/register`

**描述:** 注册新用户

**请求体:**
```json
{
  "username": "testuser",
  "password": "testpassword123",
  "email": "test@example.com"
}
```

**成功响应 (201):**
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

**验证错误响应 (400):**
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

**用户已存在响应 (409):**
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

### 2. 用户登录

**端点:** `POST /api/auth/login`

**描述:** 用户登录并获取访问令牌

**请求体:**
```json
{
  "username": "testuser",
  "password": "testpassword123"
}
```

**成功响应 (200):**
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

**认证失败响应 (401):**
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

### 3. 获取用户资料

**端点:** `GET /api/auth/profile`

**描述:** 获取当前登录用户的资料

**请求头:**
```
Authorization: Bearer <token>
```

**成功响应 (200):**
```json
{
  "code": 200,
  "message": "Profile retrieved successfully",
  "data": {
    "id": "testuser",
    "username": "testuser",
    "email": "test@example.com",
    "created_at": "2025-01-15T10:30:00Z",
    "is_active": true
  },
  "timestamp": 1703123456
}
```

**未授权响应 (401):**
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

### 4. 用户登出

**端点:** `POST /api/auth/logout`

**描述:** 用户登出（客户端清除令牌）

**请求头:**
```
Authorization: Bearer <token>
```

**成功响应 (200):**
```json
{
  "code": 200,
  "message": "Logout successful",
  "timestamp": 1703123456
}
```

## 响应格式说明

### 成功响应结构
```json
{
  "code": 200,
  "message": "Success message",
  "data": {
    // 响应数据
  },
  "timestamp": 1703123456
}
```

### 错误响应结构
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

## 验证规则

### 注册验证
- **username**: 必填，字符串
- **password**: 必填，最少6个字符
- **email**: 可选，必须是有效的邮箱格式

### 登录验证
- **username**: 必填
- **password**: 必填

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 409 | 冲突（用户已存在） |
| 500 | 服务器内部错误 |

## 使用示例

### cURL 示例

**注册用户:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword123",
    "email": "test@example.com"
  }'
```

**用户登录:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword123"
  }'
```

**获取用户资料:**
```bash
curl -X GET http://localhost:5000/api/auth/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**用户登出:**
```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```