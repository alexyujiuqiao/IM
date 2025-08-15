import os
import time
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import boto3
from functools import wraps

# Import authentication decorators
from .chat import jwt_required, get_jwt_identity

logger = logging.getLogger(__name__)

bp = Blueprint("upload", __name__, url_prefix="/api/chat/upload")

# Configuration
S3_BUCKET = os.getenv("S3_BUCKET", "im-chat-bucket")
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'm4a', 'aac', 'ogg', 'flac'}

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_unique_filename(original_filename, file_type):
    """Generate unique filename with timestamp"""
    timestamp = int(time.time())
    name, ext = os.path.splitext(original_filename)
    return f"chat-{file_type}/{name}-{timestamp}{ext}"

@bp.post("/image")
@jwt_required()
def upload_image():
    """Upload image file to S3"""
    try:
        user_id = get_jwt_identity()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                "code": 400,
                "message": "No file provided",
                "success": False
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                "code": 400,
                "message": "No file selected",
                "success": False
            }), 400
        
        # Check file extension
        if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            return jsonify({
                "code": 400,
                "message": f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}",
                "success": False
            }), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        object_key = generate_unique_filename(filename, "images")
        
        # Upload to S3
        s3 = boto3.client('s3')
        s3.upload_fileobj(file, S3_BUCKET, object_key)
        
        # Generate presigned URL
        presigned_url = s3.generate_presigned_url('get_object',
                                              Params={'Bucket': S3_BUCKET, 'Key': object_key},
                                              ExpiresIn=86400)  # 24 hours
        
        logger.info(f"Image uploaded by user {user_id}: s3://{S3_BUCKET}/{object_key}")
        
        return jsonify({
            "code": 200,
            "message": "Image uploaded successfully",
            "success": True,
            "data": {
                "s3_url": presigned_url,
                "s3_key": object_key,
                "bucket": S3_BUCKET,
                "filename": filename
            }
        })
        
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        return jsonify({
            "code": 500,
            "message": "Upload failed",
            "success": False
        }), 500

@bp.post("/audio")
@jwt_required()
def upload_audio():
    """Upload audio file to S3"""
    try:
        user_id = get_jwt_identity()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                "code": 400,
                "message": "No file provided",
                "success": False
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                "code": 400,
                "message": "No file selected",
                "success": False
            }), 400
        
        # Check file extension
        if not allowed_file(file.filename, ALLOWED_AUDIO_EXTENSIONS):
            return jsonify({
                "code": 400,
                "message": f"Invalid file type. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}",
                "success": False
            }), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        object_key = generate_unique_filename(filename, "audio")
        
        # Upload to S3
        s3 = boto3.client('s3')
        s3.upload_fileobj(file, S3_BUCKET, object_key)
        
        # Generate presigned URL
        presigned_url = s3.generate_presigned_url('get_object',
                                              Params={'Bucket': S3_BUCKET, 'Key': object_key},
                                              ExpiresIn=86400)  # 24 hours
        
        logger.info(f"Audio uploaded by user {user_id}: s3://{S3_BUCKET}/{object_key}")
        
        return jsonify({
            "code": 200,
            "message": "Audio uploaded successfully",
            "success": True,
            "data": {
                "s3_url": presigned_url,
                "s3_key": object_key,
                "bucket": S3_BUCKET,
                "filename": filename
            }
        })
        
    except Exception as e:
        logger.error(f"Audio upload failed: {e}")
        return jsonify({
            "code": 500,
            "message": "Upload failed",
            "success": False
        }), 500

@bp.post("/file")
@jwt_required()
def upload_file():
    """Upload any file to S3 (auto-detects type)"""
    try:
        user_id = get_jwt_identity()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                "code": 400,
                "message": "No file provided",
                "success": False
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                "code": 400,
                "message": "No file selected",
                "success": False
            }), 400
        
        filename = secure_filename(file.filename)
        
        # Determine file type
        if allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
            file_type = "images"
        elif allowed_file(filename, ALLOWED_AUDIO_EXTENSIONS):
            file_type = "audio"
        else:
            return jsonify({
                "code": 400,
                "message": "Unsupported file type",
                "success": False
            }), 400
        
        # Generate unique filename
        object_key = generate_unique_filename(filename, file_type)
        
        # Upload to S3
        s3 = boto3.client('s3')
        s3.upload_fileobj(file, S3_BUCKET, object_key)
        
        # Generate presigned URL
        presigned_url = s3.generate_presigned_url('get_object',
                                              Params={'Bucket': S3_BUCKET, 'Key': object_key},
                                              ExpiresIn=86400)  # 24 hours
        
        logger.info(f"File uploaded by user {user_id}: s3://{S3_BUCKET}/{object_key}")
        
        return jsonify({
            "code": 200,
            "message": "File uploaded successfully",
            "success": True,
            "data": {
                "s3_url": presigned_url,
                "s3_key": object_key,
                "bucket": S3_BUCKET,
                "filename": filename,
                "file_type": file_type
            }
        })
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        return jsonify({
            "code": 500,
            "message": "Upload failed",
            "success": False
        }), 500

@bp.get("/files")
@jwt_required()
def list_user_files():
    """List files uploaded by the current user"""
    try:
        user_id = get_jwt_identity()
        
        s3 = boto3.client('s3')
        
        # List all files in the bucket
        response = s3.list_objects_v2(Bucket=S3_BUCKET)
        
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                # You could add user-specific filtering here if needed
                files.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat(),
                    "url": s3.generate_presigned_url('get_object',
                                                  Params={'Bucket': S3_BUCKET, 'Key': obj['Key']},
                                                  ExpiresIn=3600)  # 1 hour
                })
        
        return jsonify({
            "code": 200,
            "message": "Files retrieved successfully",
            "success": True,
            "data": {
                "files": files,
                "total_count": len(files)
            }
        })
        
    except Exception as e:
        logger.error(f"List files failed: {e}")
        return jsonify({
            "code": 500,
            "message": "Failed to list files",
            "success": False
        }), 500

@bp.get("/files/user/<user_id>")
@jwt_required()
def list_user_specific_files(user_id):
    """List files for a specific user"""
    try:
        current_user_id = get_jwt_identity()
        
        s3 = boto3.client('s3')
        
        # List all files in the bucket
        response = s3.list_objects_v2(Bucket=S3_BUCKET)
        
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                # Filter for chat files only
                if obj['Key'].startswith("chat-"):
                    # Determine file type
                    file_type = "unknown"
                    if obj['Key'].startswith("chat-images/"):
                        file_type = "image"
                    elif obj['Key'].startswith("chat-audio/"):
                        file_type = "audio"
                    
                    files.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "file_type": file_type,
                        "filename": obj['Key'].split('/')[-1],
                        "url": s3.generate_presigned_url('get_object',
                                                      Params={'Bucket': S3_BUCKET, 'Key': obj['Key']},
                                                      ExpiresIn=3600)  # 1 hour
                    })
        
        return jsonify({
            "code": 200,
            "message": "User files retrieved successfully",
            "success": True,
            "data": {
                "files": files,
                "total_count": len(files),
                "requested_user_id": user_id,
                "current_user_id": current_user_id
            }
        })
        
    except Exception as e:
        logger.error(f"List user files failed: {e}")
        return jsonify({
            "code": 500,
            "message": "Failed to list user files",
            "success": False
        }), 500

 