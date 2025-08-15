from flask import Flask

from .chat import bp as chat_bp


def register_blueprints(app: Flask):
    app.register_blueprint(chat_bp) 