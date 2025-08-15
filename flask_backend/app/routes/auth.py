from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import sqlite3
import hashlib
import os
import time
from pathlib import Path
import logging
from ..utils.api_response import (
    success_response, 
    error_response, 
    auth_response, 
    validation_error
)

# ---------------------------------------------------------------------------
# Configure module-level logger. The main application (app/__init__.py) may
# configure logging separately; `force=True` ensures this does not add
# duplicate handlers when the module is reloaded under the dev server.
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.DEBUG,
    force=True,
)

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def get_db_path():
    """Get the database path"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.db")

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username: str, password: str) -> bool:
    """Verify user credentials and log the outcome."""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        password_hash = hash_password(password)

        cursor.execute(
            """
            SELECT id FROM users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
            """,
            (username, password_hash),
        )

        user = cursor.fetchone()
        conn.close()

        logger.debug("verify_user: username=%s exists=%s", username, bool(user))
        return user is not None
    except Exception as e:
        logger.exception("Error verifying user credentials for '%s'", username)
        return False

@bp.post("/login")
def login():
    """Handle user login with standard REST API format."""
    logger.debug("/login endpoint called. Headers=%s", dict(request.headers))

    data = request.get_json()

    if not data:
        logger.warning("/login called with no JSON body.")
        return validation_error("request", "No data provided", 400)

    username = data.get("username")
    password = data.get("password")

    logger.debug("/login payload username=%s password_length=%d", username, len(password) if password else 0)

    if not username:
        logger.warning("/login missing username.")
        return validation_error("username", "Username is required", 400)
    
    if not password:
        logger.warning("/login missing password.")
        return validation_error("password", "Password is required", 400)

    if verify_user(username, password):
        logger.info("User '%s' authenticated successfully.", username)
        
        # Get user details for response
        try:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, email, created_at, is_active 
                FROM users WHERE username = ?
            ''', (username,))
            
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                user_info = {
                    "id": username,  # Using username as ID for simplicity
                    "username": user_data[0],
                    "email": user_data[1],
                    "created_at": user_data[2],
                    "is_active": bool(user_data[3])
                }
            else:
                user_info = {
                    "id": username,
                    "username": username,
                    "is_active": True
                }
        except Exception as e:
            logger.warning("Could not fetch user details: %s", e)
            user_info = {
                "id": username,
                "username": username,
                "is_active": True
            }
        
        # Create access token
        access_token = create_access_token(identity=username)
        
        return auth_response(
            token=access_token,
            user=user_info,
            message="Login successful"
        )
    else:
        logger.warning("Invalid credentials for user '%s'", username)
        return error_response(
            message="Invalid credentials",
            code=401,
            errors=[{
                "status": "401",
                "title": "Authentication Failed",
                "detail": "Invalid username or password"
            }]
        )

@bp.post("/register")
def register():
    """Handle user registration with standard REST API format"""
    data = request.get_json()
    
    if not data:
        return validation_error("request", "No data provided", 400)
    
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    
    # Validate required fields
    if not username:
        return validation_error("username", "Username is required", 400)
    
    if not password:
        return validation_error("password", "Password is required", 400)
    
    # Validate password strength
    if len(password) < 6:
        return validation_error("password", "Password must be at least 6 characters long", 400)
    
    # Validate email format if provided
    if email and '@' not in email:
        return validation_error("email", "Invalid email format", 400)
    
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return error_response(
                message="Registration failed",
                code=409,
                errors=[{
                    "status": "409",
                    "title": "User Already Exists",
                    "detail": "Username already exists"
                }]
            )
        
        # Check if email already exists (if email provided)
        if email:
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                conn.close()
                return error_response(
                    message="Registration failed",
                    code=409,
                    errors=[{
                        "status": "409",
                        "title": "Email Already Exists",
                        "detail": "Email already registered"
                    }]
                )
        
        # Create new user
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash, email)
            VALUES (?, ?, ?)
        ''', (username, password_hash, email))
        
        conn.commit()
        conn.close()
        
        # Return success response with user data
        user_data = {
            "id": username,
            "username": username,
            "email": email,
            "created_at": int(time.time()),
            "is_active": True
        }
        
        return success_response(
            data=user_data,
            message="User registered successfully",
            code=201
        )
        
    except Exception as e:
        logger.error("Registration failed: %s", e)
        return error_response(
            message="Registration failed",
            code=500,
            errors=[{
                "status": "500",
                "title": "Internal Server Error",
                "detail": "An error occurred during registration"
            }]
        )

@bp.get("/profile")
@jwt_required()
def get_profile():
    """Get current user profile with standard REST API format"""
    current_user = get_jwt_identity()
    
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, email, created_at, is_active 
            FROM users WHERE username = ?
        ''', (current_user,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            user_data = {
                "id": current_user,
                "username": user[0],
                "email": user[1],
                "created_at": user[2],
                "is_active": bool(user[3])
            }
            
            return success_response(
                data=user_data,
                message="Profile retrieved successfully",
                code=200
            )
        else:
            return error_response(
                message="User not found",
                code=404,
                errors=[{
                    "status": "404",
                    "title": "User Not Found",
                    "detail": "User profile not found"
                }]
            )
            
    except Exception as e:
        logger.error("Error retrieving profile: %s", e)
        return error_response(
            message="Error retrieving profile",
            code=500,
            errors=[{
                "status": "500",
                "title": "Internal Server Error",
                "detail": "An error occurred while retrieving profile"
            }]
        )

@bp.post("/logout")
@jwt_required()
def logout():
    """Handle user logout with standard REST API format"""
    return success_response(
        message="Logout successful",
        code=200
    ) 

@bp.post("/upload-avatar")
@jwt_required()
def upload_profile_picture():
    """Handle profile picture uploads with validation"""
    current_user = get_jwt_identity()
    
    # Check if file is present
    if 'file' not in request.files:
        return validation_error("file", "No file uploaded", 400)
    
    file = request.files['file']
    
    # Basic file validation
    if file.filename == '':
        return validation_error("file", "No selected file", 400)
    
    # Validate file type
    allowed_types = {'image/jpeg', 'image/png', 'image/gif'}
    if file.mimetype not in allowed_types:
        return validation_error("file", "Only JPEG, PNG, and GIF allowed", 400)
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    file_data = file.read()
    if len(file_data) > max_size:
        return validation_error("file", "File exceeds 10MB limit", 400)
    
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # Store image as BLOB in database
        cursor.execute('''
            UPDATE users 
            SET profile_picture = ?
            WHERE username = ?
        ''', (sqlite3.Binary(file_data), current_user))
        
        conn.commit()
        conn.close()
        
        return success_response(
            message="Profile picture updated successfully",
            code=200
        )
    except Exception as e:
        logger.error("Error updating profile picture: %s", e)
        return error_response(
            message="Failed to update profile picture",
            code=500,
            errors=[{
                "status": "500",
                "title": "Database Error",
                "detail": "Could not save image to database"
            }]
        )
