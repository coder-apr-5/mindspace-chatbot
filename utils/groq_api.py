import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Load local environment variables if present
load_dotenv()

SYSTEM_PROMPT = (
    "You are MindSpace, a compassionate mental health companion for students. "
    "You are NOT a therapist. You listen actively, validate feelings, ask gentle "
    "follow-up questions, and offer evidence-based coping tips when appropriate. "
    "Never diagnose. Always encourage professional help for serious concerns. "
    "Keep responses to 3-5 warm, conversational sentences. Occasionally suggest "
    "a breathing exercise, grounding technique, or journaling prompt when the user "
    "seems distressed. "
    "CRITICAL: If the user says they are not comfortable with a recommendation, or that it is not working, "
    "immediately validate their feelings, apologize, and recommend a completely different outcome/technique "
    "(e.g., if they dislike breathing exercises, switch to physical progressive muscle relaxation, grounding, or journaling)."
)

def get_api_key() -> str:
    """
    Retrieves the Groq API key from streamlit secrets, falling back to
    environment variables or python-dotenv. Returns empty string if not found.
    """
    try:
        # First check st.secrets
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    
    # Fallback to system environment variable
    return os.environ.get("GROQ_API_KEY", "")

def get_chat_response(conversation_history: list) -> str:
    """
    Sends the full conversation history to Groq and returns the model reply.
    Prepend system prompt to the messages.
    """
    api_key = get_api_key()
    if not api_key:
        return "⚠️ **Configuration Error**: `GROQ_API_KEY` was not found. Please add it to your Hugging Face Space Secrets or create a `.env` file locally."

    try:
        client = Groq(api_key=api_key)
        
        # Prepare messages: inject system prompt as first message
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Format conversation history
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1024,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ **Error communicating with AI service**: {str(e)}"
