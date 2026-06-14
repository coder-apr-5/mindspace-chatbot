import streamlit as st
import html
import re
from utils.groq_api import get_chat_response, get_api_key
from utils.mood_detector import detect_mood
from utils.tip_cards import TIPS
from utils.crisis_keywords import check_for_crisis, CRISIS_BANNER_HTML

# Page Configuration
st.set_page_config(
    page_title="MindSpace — Student Mental Health Companion",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom styling block to override default fonts and layouts
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@300;400;500;600&display=swap');

/* Main app background and global font resets */
.stApp {
    background-color: #1C1F2E !important;
    color: #F3F4F6 !important;
}

[data-testid="stHeader"] {
    background-color: rgba(28, 31, 46, 0.8) !important;
    backdrop-filter: blur(8px);
}

[data-testid="stSidebar"] {
    background-color: #252A3D !important;
    border-right: 1px solid #312E6B !important;
}

/* Headings */
h1, h2, h3, h4, h5, h6, .brand-title {
    font-family: 'DM Serif Display', serif !important;
    font-weight: 400;
}

/* Body and UI Elements */
p, span, label, div, button, input, textarea {
    font-family: 'Inter', sans-serif !important;
}

/* Custom Chat Container styling */
.chat-log {
    margin-top: 10px;
    margin-bottom: 80px;
}

/* Hide default streamlit user/assistant avatars if using native widgets */
/* But we are using custom HTML chat widgets, so we handle formatting ourselves */
</style>
""", unsafe_allow_html=True)

# Mood Metadata for Emoji, Labels, and Theme Colors
MOOD_METADATA = {
    "happy": {"emoji": "😊", "label": "Happy", "color": "#34D399"},
    "neutral": {"emoji": "😐", "label": "Neutral", "color": "#94A3B8"},
    "anxious": {"emoji": "😰", "label": "Anxious", "color": "#F59E0B"},
    "sad": {"emoji": "😢", "label": "Sad", "color": "#60A5FA"},
    "stressed": {"emoji": "😫", "label": "Stressed", "color": "#F87171"},
    "lonely": {"emoji": "👤", "label": "Lonely", "color": "#C084FC"},
    "overwhelmed": {"emoji": "🤯", "label": "Overwhelmed", "color": "#FB923C"}
}

def markdown_to_html(text: str) -> str:
    """
    Safely escapes text and parses basic Markdown rules (bold, italics, bullets, newlines)
    for rendering inside custom HTML bubbles.
    """
    # 1. Escape HTML
    escaped = html.escape(text)
    
    # 2. Convert bold (supports **bold** and __bold__)
    escaped = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped)
    escaped = re.sub(r'__(.*?)__', r'<strong>\1</strong>', escaped)
    
    # 3. Convert italics (supports *italic* and _italic_)
    escaped = re.sub(r'\*(.*?)\*', r'<em>\1</em>', escaped)
    escaped = re.sub(r'_(.*?)_', r'<em>\1</em>', escaped)
    
    # 4. Handle bullets
    lines = escaped.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('- '):
            lines[i] = f"• {stripped[2:]}"
        elif stripped.startswith('* '):
            lines[i] = f"• {stripped[2:]}"
            
    escaped = '\n'.join(lines)
    
    # 5. Convert newlines to breaks
    escaped = escaped.replace('\n', '<br>')
    return escaped

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I'm MindSpace, your companion. How are you feeling today? Remember, you can talk to me about school, stress, or anything on your mind. I'm here to listen.",
            "show_tip": False,
            "tip_mood": "neutral"
        }
    ]
if "mood_history" not in st.session_state:
    st.session_state.mood_history = []
if "crisis_triggered" not in st.session_state:
    st.session_state.crisis_triggered = False
if "current_mood" not in st.session_state:
    st.session_state.current_mood = {"mood": "neutral", "intensity": "low"}

# SIDEBAR IMPLEMENTATION
with st.sidebar:
    st.markdown("<h1 class='brand-title' style='margin-bottom: 0; color: #A78BFA;'>🌿 MindSpace</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-style: italic; color: #94A3B8; margin-top: 0; margin-bottom: 25px;'>Your student mental health companion</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid #312E6B;'>", unsafe_allow_html=True)
    
    # Mood History Timeline
    st.markdown("<h3 style='color: #A78BFA; font-size: 18px; margin-bottom: 10px;'>📈 Mood Timeline</h3>", unsafe_allow_html=True)
    if st.session_state.mood_history:
        trail_parts = []
        # Take the last 6 moods from the list
        last_moods = st.session_state.mood_history[-6:]
        for m in last_moods:
            meta = MOOD_METADATA.get(m["mood"], MOOD_METADATA["neutral"])
            trail_parts.append(f"{meta['emoji']} {meta['label']}")
        trail_str = " → ".join(trail_parts)
        st.markdown(
            f"<div style='font-size: 13px; color: #E5E7EB; background-color: #1C1F2E; "
            f"padding: 12px; border-radius: 8px; border: 1px solid #312E6B; "
            f"line-height: 1.5; word-break: break-word;'>"
            f"{trail_str}"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown("<p style='font-size: 13px; color: #94A3B8; font-style: italic;'>No moods recorded yet. Start chatting!</p>", unsafe_allow_html=True)
        
    st.markdown("<hr style='border: 1px solid #312E6B;'>", unsafe_allow_html=True)
    
    # Quick-Relief Buttons
    st.markdown("<h3 style='color: #A78BFA; font-size: 18px; margin-bottom: 10px;'>⚡ Quick Relief</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 12px; color: #94A3B8; margin-bottom: 15px;'>Need to unwind right now? Trigger a quick exercise inline:</p>", unsafe_allow_html=True)
    
    if st.button("💨 Box Breathing", use_container_width=True):
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"### 💨 Quick Box Breathing\n{TIPS['anxious']['content']}",
            "show_tip": False,
            "tip_mood": "anxious"
        })
        st.rerun()
        
    if st.button("🧘 Grounding Exercise", use_container_width=True):
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"### 🧘 Quick 5-4-3-2-1 Grounding\n{TIPS['stressed']['content']}",
            "show_tip": False,
            "tip_mood": "stressed"
        })
        st.rerun()
        
    if st.button("📝 Journaling Prompt", use_container_width=True):
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"### 📝 Quick Gratitude Journaling\n{TIPS['sad']['content']}",
            "show_tip": False,
            "tip_mood": "sad"
        })
        st.rerun()
        
    st.markdown("<hr style='border: 1px solid #312E6B;'>", unsafe_allow_html=True)
    
    # Reset Session Button
    if st.button("🗑️ Clear Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()
        
    # Disclaimer Text
    st.markdown(
        "<div style='font-size: 11px; color: #94A3B8; margin-top: 30px; border-top: 1px solid #312E6B; padding-top: 15px; line-height: 1.4;'>"
        "⚠️ <strong>Disclaimer</strong>: MindSpace is not a substitute for professional mental health care, clinical therapy, or medical diagnosis. "
        "Always encourage professional help for serious concerns."
        "</div>",
        unsafe_allow_html=True
    )

# MAIN CHAT APPLICATION

# Header Title
st.markdown("<h1 style='margin-top: 0; color: #A78BFA; font-size: 2.5rem;'>🌿 MindSpace</h1>", unsafe_allow_html=True)

# 1. CRISIS SAFETY BANNER (Rendered at top of main view if triggered)
if st.session_state.crisis_triggered:
    st.markdown(CRISIS_BANNER_HTML, unsafe_allow_html=True)

# 2. LIVE MOOD BADGE
current_mood_data = st.session_state.current_mood
meta = MOOD_METADATA.get(current_mood_data["mood"], MOOD_METADATA["neutral"])
intensity_label = current_mood_data["intensity"].upper()

badge_html = f"""
<div style="
    display: inline-flex;
    align-items: center;
    background-color: {meta['color']}1A; /* 10% opacity */
    border: 1px solid {meta['color']};
    color: {meta['color']};
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 20px;
">
    <span style="margin-right: 6px; font-size: 15px;">{meta['emoji']}</span>
    Current State: {meta['label']} ({intensity_label} Intensity)
</div>
"""
st.markdown(badge_html, unsafe_allow_html=True)

# Render Chat Log
chat_placeholder = st.container()

with chat_placeholder:
    for idx, msg in enumerate(st.session_state.messages):
        role = msg["role"]
        content_html = markdown_to_html(msg["content"])
        
        if role == "user":
            # Right-aligned purple-tint bubble
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; width: 100%; margin: 10px 0;">
                <div style="
                    background-color: #312E6B;
                    color: #F5F3FF;
                    padding: 12px 18px;
                    border-radius: 18px 18px 0px 18px;
                    max-width: 75%;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
                    font-size: 15px;
                    line-height: 1.5;
                ">
                    {content_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            # Left-aligned dark card with lavender left border
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; width: 100%; margin: 10px 0;">
                <div style="
                    background-color: #252A3D;
                    color: #E5E7EB;
                    padding: 12px 18px;
                    border-radius: 18px 18px 18px 0px;
                    border-left: 3px solid #A78BFA;
                    max-width: 75%;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
                    font-size: 15px;
                    line-height: 1.5;
                ">
                    {content_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show Tip Card if flag is set for this message
            if msg.get("show_tip") and msg.get("tip_mood") in TIPS:
                tip = TIPS[msg["tip_mood"]]
                tip_content_html = markdown_to_html(tip["content"])
                
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; width: 100%; margin: -4px 0 16px 0;">
                    <details open style="
                        background-color: #252A3D;
                        border: 1px solid #A78BFA;
                        border-radius: 8px;
                        padding: 12px 16px;
                        width: 75%;
                        color: #E5E7EB;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    ">
                        <summary style="
                            font-weight: 600;
                            cursor: pointer;
                            color: #A78BFA;
                            outline: none;
                            display: flex;
                            align-items: center;
                        ">
                            💡 Recommended Exercise
                        </summary>
                        <div style="margin-top: 10px; font-size: 14px; line-height: 1.5; border-top: 1px solid #312E6B; padding-top: 10px;">
                            <strong style="font-size: 15px; color: #F3F4F6;">{tip['title']}</strong>
                            <p style="margin: 4px 0 10px 0; color: #94A3B8; font-style: italic;">{tip['description']}</p>
                            {tip_content_html}
                        </div>
                    </details>
                </div>
                """, unsafe_allow_html=True)

# User Input Box
user_input = st.chat_input("Talk to MindSpace...")

if user_input:
    # 1. Immediate Safety Check (Crisis scan)
    if check_for_crisis(user_input):
        st.session_state.crisis_triggered = True
        
    # 2. Append User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 3. Dynamic Mood Classification & Timeline Addition
    # We pass the conversation history (including this new message) to Groq
    detected = detect_mood(st.session_state.messages)
    st.session_state.current_mood = detected
    
    # Only append to timeline if it represents actual change or new info (we track all interactions)
    st.session_state.mood_history.append(detected)
    
    # 4. Generate AI reply with spinner
    with st.spinner("MindSpace is listening..."):
        ai_reply = get_chat_response(st.session_state.messages)
        
    # 5. Determine if we should recommend a relaxation card
    # Should recommend on medium/high negative states
    negative_moods = ["anxious", "sad", "stressed", "lonely", "overwhelmed"]
    show_tip = False
    if detected["mood"] in negative_moods and detected["intensity"] in ["medium", "high"]:
        show_tip = True
        
    # 6. Append Assistant Reply
    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_reply,
        "show_tip": show_tip,
        "tip_mood": detected["mood"]
    })
    
    # Trigger Streamlit rerun to display updates
    st.rerun()
