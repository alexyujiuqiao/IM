import gradio as gr
import requests
import json
import base64
import logging
import os
import sys

# ------------------------------------------------------------
# CLI flag --no-auth (skip login/registration UI)
# ------------------------------------------------------------
NO_AUTH = "--no-auth" in sys.argv

# Local helper that wraps all API calls
from chat_client import ChatClient

# --- Logging setup ---------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
    force=True
)

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:5050")
MOBILE_API_URL = f"{BASE_URL}/api/chat/v1/mobile"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
REGISTER_URL = f"{BASE_URL}/api/auth/register"

def file_to_base64(filepath):
    if filepath is None:
        return None
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode()

def chat_fn(message, history, token, image_file, audio_input):
    """Handle chat submission and update history state."""
    # Use mobile endpoint by setting use_mobile_endpoint=True
    client = ChatClient(token, use_mobile_endpoint=True)
    
    # Convert Gradio history (tuples) to OpenAI format for API
    openai_history = []
    if history:
        for user_msg, assistant_msg in history:
            if user_msg:
                openai_history.append({"role": "user", "content": user_msg})
            if assistant_msg:
                openai_history.append({"role": "assistant", "content": assistant_msg})
    
    try:
        reply, is_audio, transcription = client.chat(
            user_message=message,
            history=openai_history,  # Pass OpenAI format to API
            image_file=image_file,
            audio_file=audio_input,
        )
    except Exception as e:
        reply, is_audio, transcription = f"Error: {e}", False, None

    # Build new history in Gradio tuple format
    updated_history = history or []
    
    # Add user message
    user_content = message
    if image_file:
        user_content = (image_file, "image")  # Gradio image format
    
    # Add assistant response
    assistant_content = reply
    if is_audio:
        filename = f"response_{len(history)}.mp3"
        with open(filename, "wb") as f:
            f.write(reply)
        assistant_content = (filename, "audio/mpeg")  # Gradio audio format
    
    # Add the new exchange as a tuple
    updated_history.append([user_content, assistant_content])

    return updated_history, updated_history, ""

# Simple unified UI
with gr.Blocks() as demo:
    gr.Markdown("# IM Chat Companion")
    
    with gr.Row():
        with gr.Column():
            # Authentication (only if not in no-auth mode)
            if not NO_AUTH:
                with gr.Group():
                    username = gr.Textbox(label="Username")
                    password = gr.Textbox(label="Password", type="password")
                    login_btn = gr.Button("Login")
                    token = gr.State("")
            
            # Chat interface
            chatbot = gr.Chatbot(height=400)
            msg = gr.Textbox(label="Message")
            with gr.Row():
                image_file = gr.Image(sources=["upload"], type="filepath", label="Image")
                audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Audio")
            send = gr.Button("Send")
            state = gr.State([])

    # Event handlers
    if not NO_AUTH:
        def login_fn(username, password):
            try:
                resp = requests.post(LOGIN_URL, json={"username": username, "password": password})
                resp.raise_for_status()
                data = resp.json()
                token = data.get("data", {}).get("attributes", {}).get("token", "")
                return token, "Login successful!" if token else "Login failed"
            except Exception as e:
                return "", f"Login error: {e}"
        
        login_btn.click(login_fn, [username, password], [token, msg])

    send.click(chat_fn, [msg, state, token, image_file, audio_input], [chatbot, state, msg])
    msg.submit(chat_fn, [msg, state, token, image_file, audio_input], [chatbot, state, msg])

if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860) 
