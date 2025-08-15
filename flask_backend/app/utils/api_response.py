"""
Standardized API Response Utilities
遵循 JSON API 规范和最佳实践的响应格式
"""

import time
import uuid
from typing import Any, Dict, List, Optional, Union
from flask import jsonify

class APIResponse:
    """Standardized API response builder following JSON API specification."""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        code: int = 200,
        meta: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Build a successful API response.
        
        Args:
            data: Response data
            message: Success message
            code: HTTP status code
            meta: Additional metadata
            
        Returns:
            Standardized success response
        """
        response = {
            "code": code,
            "message": message,
            "timestamp": int(time.time())
        }
        
        if data is not None:
            response["data"] = data
            
        if meta:
            response["meta"] = meta
            
        return response
    
    @staticmethod
    def error(
        message: str = "Error",
        code: int = 400,
        errors: Optional[List[Dict]] = None,
        meta: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Build an error API response.
        
        Args:
            message: Error message
            code: HTTP status code
            errors: List of detailed errors
            meta: Additional metadata
            
        Returns:
            Standardized error response
        """
        response = {
            "code": code,
            "message": message,
            "timestamp": int(time.time())
        }
        
        if errors:
            response["errors"] = errors
            
        if meta:
            response["meta"] = meta
            
        return response
    
    @staticmethod
    def chat_response(
        content: str,
        voice_profile: Optional[str] = None,
        model: str = "im-chat",
        usage: Optional[Dict] = None,
        audio_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a standardized chat response.
        
        Args:
            content: Assistant's response content
            voice_profile: Detected voice profile
            model: Model used for generation
            usage: Token usage information
            audio_url: Audio response URL (if applicable)
            
        Returns:
            Standardized chat response
        """
        data = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "type": "chat.completion",
            "attributes": {
                "content": content,
                "created_at": int(time.time())
            }
        }
        
        if voice_profile:
            data["attributes"]["voice_profile"] = voice_profile
            
        if audio_url:
            data["attributes"]["audio_url"] = audio_url
        
        meta = {
            "model": model
        }
        
        if usage:
            meta["usage"] = usage
            
        return APIResponse.success(
            data=data,
            message="Chat response generated successfully",
            code=200,
            meta=meta
        )
    
    @staticmethod
    def auth_response(
        token: str,
        user: Dict[str, Any],
        message: str = "Authentication successful"
    ) -> Dict[str, Any]:
        """
        Build a standardized authentication response.
        
        Args:
            token: JWT token
            user: User information
            message: Success message
            
        Returns:
            Standardized auth response
        """
        data = {
            "type": "authentication",
            "attributes": {
                "token": token,
                "user": user,
                "created_at": int(time.time())
            }
        }
        
        return APIResponse.success(
            data=data,
            message=message,
            code=200
        )
    
    @staticmethod
    def validation_error(
        field: str,
        detail: str,
        code: int = 422
    ) -> Dict[str, Any]:
        """
        Build a validation error response.
        
        Args:
            field: Field that failed validation
            detail: Validation error detail
            code: HTTP status code
            
        Returns:
            Standardized validation error response
        """
        errors = [
            {
                "status": str(code),
                "source": {"pointer": f"/data/attributes/{field}"},
                "title": "Validation Error",
                "detail": detail
            }
        ]
        
        return APIResponse.error(
            message="Validation failed",
            code=code,
            errors=errors
        )

def json_response(data: Dict[str, Any], status_code: int = 200):
    """
    Create a Flask JSON response with proper headers.
    
    Args:
        data: Response data
        status_code: HTTP status code
        
    Returns:
        Flask JSON response
    """
    response = jsonify(data)
    response.status_code = status_code
    response.headers['Content-Type'] = 'application/json'
    return response

def success_response(
    data: Any = None,
    message: str = "Success",
    code: int = 200,
    meta: Optional[Dict] = None
):
    """Create a successful Flask response."""
    response_data = APIResponse.success(data, message, code, meta)
    return json_response(response_data, code)

def error_response(
    message: str = "Error",
    code: int = 400,
    errors: Optional[List[Dict]] = None,
    meta: Optional[Dict] = None
):
    """Create an error Flask response."""
    response_data = APIResponse.error(message, code, errors, meta)
    return json_response(response_data, code)

def chat_response(
    content: str,
    voice_profile: Optional[str] = None,
    model: str = "im-chat",
    usage: Optional[Dict] = None,
    audio_url: Optional[str] = None
):
    """Create a chat Flask response."""
    response_data = APIResponse.chat_response(
        content, voice_profile, model, usage, audio_url
    )
    return json_response(response_data, 200)

def auth_response(
    token: str,
    user: Dict[str, Any],
    message: str = "Authentication successful"
):
    """Create an authentication Flask response."""
    response_data = APIResponse.auth_response(token, user, message)
    return json_response(response_data, 200)

def validation_error(
    field: str,
    detail: str,
    code: int = 422
):
    """Create a validation error Flask response."""
    response_data = APIResponse.validation_error(field, detail, code)
    return json_response(response_data, code) 