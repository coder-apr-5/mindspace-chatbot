import os
import streamlit as st
import datetime
from dotenv import load_dotenv
from groq import Groq

# Load local environment variables if present
load_dotenv()

def get_system_prompt(bot_name="MindSpace"):
    return f"""You are {bot_name}, a highly empathetic, compassionate, and knowledgeable AI mental health companion. 
Your purpose is to provide a safe, judgment-free space for the user to express their thoughts and feelings.

KEY GUIDELINES:
1. Empathy First: Always validate the user's feelings. Use phrases like "I hear you", "That sounds really difficult", or "It's completely normal to feel that way".
2. Active Listening: Reflect back what you hear to show understanding.
3. Constructive Guidance: Offer gentle, actionable advice only after validating their emotions. Focus on grounding techniques, mindfulness, and healthy coping mechanisms.
4. Boundaries & Safety: You are an AI, not a licensed therapist. If the user mentions self-harm, severe depression, or crisis, strongly but gently encourage them to seek professional help or contact emergency services.
5. Tone: Warm, supportive, calm, and conversational. Avoid sounding clinical or robotic.
6. Identity: You are {bot_name}. Never break character. Never say "I am a large language model" or "As an AI".

Remember, your goal is to help the user feel heard, supported, and a little bit better than they felt before talking to you.
"""

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

def get_chat_response(conversation_history: list, user_data: dict = None) -> str:
    """
    Sends the full conversation history to Groq and returns the model reply.
    Prepend system prompt to the messages.
    """
    api_key = get_api_key()
    if not api_key:
        return "⚠️ **Configuration Error**: `GROQ_API_KEY` was not found. Please add it to your Hugging Face Space Secrets or create a `.env` file locally."

    try:
        client = Groq(api_key=api_key)
        
        bot_name = user_data.get('bot_name', 'MindSpace') if user_data else 'MindSpace'
        dynamic_prompt = get_system_prompt(bot_name)
        if user_data:
            dynamic_prompt += "\n\nInformation about the user you are talking to:\n"
            dynamic_prompt += f"- Name: {user_data.get('display_name', 'Unknown')}\n"
            if user_data.get('dob'):
                dynamic_prompt += f"- Date of Birth: {user_data.get('dob')}\n"
            if user_data.get('career_level'):
                dynamic_prompt += f"- Career Level: {user_data.get('career_level')}\n"
            if user_data.get('study_info'):
                dynamic_prompt += f"- Study/Work Info: {user_data.get('study_info')}\n"
            
            # Add historical mood context if it exists in session_state
            if "mood_history" in st.session_state and len(st.session_state.mood_history) > 0:
                recent_moods = [m["mood"] if isinstance(m, dict) else str(m) for m in st.session_state.mood_history[-5:]]
                dynamic_prompt += f"- Recent Mood History: {', '.join(recent_moods)}\n"

            dynamic_prompt += "\nUse this context to personalize your responses naturally. Mention their name occasionally, and tailor advice to their career/study level. Reference their recent mood trends if appropriate."

        # Inject real-time clock
        now = datetime.datetime.now()
        dynamic_prompt += f"\n\n[SYSTEM INFO] The current date and time is: {now.strftime('%A, %B %d, %Y %I:%M %p')}. If the user asks for the time, provide it confidently."

        # Prepare messages: inject system prompt as first message
        messages = [{"role": "system", "content": dynamic_prompt}]
        
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
