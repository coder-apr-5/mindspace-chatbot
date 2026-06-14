import json
import re
import streamlit as st
from groq import Groq
from utils.groq_api import get_api_key

MOOD_SYSTEM_PROMPT = (
    "Respond ONLY with valid JSON, no explanation, no markdown, no extra text:\n"
    "{\n"
    '  "mood": "happy"|"neutral"|"anxious"|"sad"|"stressed"|"lonely"|"overwhelmed",\n'
    '  "intensity": "low"|"medium"|"high"\n'
    "}"
)

def parse_json_safely(text: str) -> dict:
    """
    Cleans up the LLM response (handling markdown code blocks if any)
    and loads it as JSON.
    """
    cleaned = text.strip()
    # Remove markdown code fencing if returned
    if cleaned.startswith("```"):
        # Match ```json ... ``` or just ``` ... ```
        match = re.search(r"```(?:json)?\s+(.*?)\s+```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)
        else:
            cleaned = cleaned.replace("```json", "").replace("```", "")
    
    cleaned = cleaned.strip()
    return json.loads(cleaned)

def detect_mood(conversation_history: list) -> dict:
    """
    Calls Groq to classify the user's current mood based on the full conversation history.
    Returns: dict with 'mood' and 'intensity'.
    Fallback: {'mood': 'neutral', 'intensity': 'low'}
    """
    fallback = {"mood": "neutral", "intensity": "low"}
    
    api_key = get_api_key()
    if not api_key:
        return fallback

    try:
        client = Groq(api_key=api_key)
        
        # Inject mood classification prompt as the system instructions
        messages = [{"role": "system", "content": MOOD_SYSTEM_PROMPT}]
        
        # Add full conversation history to give context
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        # Call Groq with temperature=0 and short token count
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=50,
            temperature=0.0
        )
        
        raw_content = response.choices[0].message.content
        result = parse_json_safely(raw_content)
        
        # Validate result has the right structure
        valid_moods = ["happy", "neutral", "anxious", "sad", "stressed", "lonely", "overwhelmed"]
        valid_intensities = ["low", "medium", "high"]
        
        mood = result.get("mood", "neutral").lower()
        intensity = result.get("intensity", "low").lower()
        
        if mood not in valid_moods:
            mood = "neutral"
        if intensity not in valid_intensities:
            intensity = "low"
            
        return {"mood": mood, "intensity": intensity}
        
    except Exception as e:
        # Gracefully handle parse or API errors by falling back to neutral
        return fallback
