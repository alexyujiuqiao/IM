from flask import Flask
from flask_jwt_extended import JWTManager
import os

# Import blueprints lazily to avoid circular deps when tests stub modules
try:
    from .routes.chat import bp as chat_bp
except ImportError as e:
    print(f"Failed to import chat_bp: {e}")
    chat_bp = None

try:
    from .routes.auth import bp as auth_bp
except ImportError as e:
    print(f"Failed to import auth_bp: {e}")
    auth_bp = None

try:
    from .routes.upload import bp as upload_bp
except ImportError as e:
    print(f"Failed to import upload_bp: {e}")
    upload_bp = None

def create_app() -> Flask:
    """Application factory with JWT and authentication support."""
    app = Flask(__name__)

    # Basic default config – feel free to override via environment variables
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev_secret"))
    app.config.setdefault("JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "jwt_secret"))
    app.config.setdefault("JWT_ACCESS_TOKEN_EXPIRES", 3600)  # 1 hour
    # Optional auth toggle: export DISABLE_AUTH=true to bypass JWT validation
    disable_auth = os.getenv("DISABLE_AUTH", "false").lower() in ("1", "true", "yes")
    app.config["DISABLE_AUTH"] = disable_auth

    # Initialize JWT
    jwt = JWTManager(app)

    # Register blueprints (skip auth if disabled)
    if not disable_auth and auth_bp is not None:
        app.register_blueprint(auth_bp)
    
    if chat_bp is not None:
        app.register_blueprint(chat_bp)
    
    if upload_bp is not None:
        app.register_blueprint(upload_bp)
    
    # Removed rag_chat and mobile_chat blueprints as they have been deprecated.

    # Simple health-check route
    @app.get("/health")
    def _health():
        return {"status": "ok"}, 200

    return app 