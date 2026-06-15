import streamlit as st
import html
import re
import time
import datetime
import base64
import os
import requests
from dotenv import load_dotenv

from utils.db import create_user, get_user_by_username, get_user_by_email, verify_user, update_user_onboarding, save_message, get_user_messages, save_mood, get_user_moods, delete_user_history
from utils.auth import hash_password, verify_password, check_password_strength, is_valid_email, generate_verification_code, send_verification_email

from utils.groq_api import get_chat_response, get_api_key
from utils.mood_detector import detect_mood
from utils.tip_cards import TIPS
from utils.crisis_keywords import check_for_crisis, CRISIS_BANNER_HTML

load_dotenv()

# Function to get base64 of image
@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Google OAuth Utils
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

def get_google_auth_url():
    redirect_uri = "http://localhost:8501"
    scope = "openid email profile"
    url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"
    return url

def get_google_button_html():
    return f"""
    <a href="{get_google_auth_url()}" target="_self" style="text-decoration: none; width: 100%; display: block; margin-top: 10px;">
        <div style="display: flex; align-items: center; justify-content: center; background-color: white; color: #3c4043; font-family: 'Roboto', sans-serif; font-weight: 500; height: 44px; border-radius: 8px; box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15); cursor: pointer; transition: all 0.2s;">
            <div style="margin-right: 12px; display: flex; align-items: center;">
                <svg version="1.1" xmlns="http://www.w3.org/2000/svg" width="18px" height="18px" viewBox="0 0 48 48"><g><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path><path fill="none" d="M0 0h48v48H0z"></path></g></svg>
            </div>
            <span style="font-size: 15px;">Sign in with Google</span>
        </div>
    </a>
    <style>
        div:hover > svg {{ transform: scale(1.05); }}
    </style>
    """

def authenticate_google_code(code):
    redirect_uri = "http://localhost:8501"
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    r = requests.post(token_url, data=data)
    if r.status_code == 200:
        access_token = r.json().get("access_token")
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_r = requests.get(user_info_url, headers=headers)
        if user_info_r.status_code == 200:
            return user_info_r.json()
    return None

# Page Configuration
st.set_page_config(
    page_title="MindSpace — Student Mental Health Companion",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Handle Google OAuth Callback via Query Params
if "code" in st.query_params:
    code = st.query_params["code"]
    st.query_params.clear() # Clear it so it doesn't run again
    
    with st.spinner("Authenticating with Google..."):
        user_info = authenticate_google_code(code)
        if user_info:
            email = user_info.get("email")
            name = user_info.get("name", "Google User")
            user = get_user_by_email(email)
            if not user:
                create_user(username=email, email=email, password_hash="", auth_provider="google", is_verified=True, display_name=name)
                user = get_user_by_email(email)
                
            st.session_state.current_user = user
            if not user.get('onboarding_completed', False):
                st.session_state.app_page = "onboarding"
            else:
                st.session_state.app_page = "chatbot"
            st.rerun()
        else:
            st.error("Failed to authenticate with Google. Please check your credentials.")

# Pre-load the brain image
brain_image_path = os.path.join("assets", "intro_logo.png")
if os.path.exists(brain_image_path):
    brain_b64 = get_base64_of_bin_file(brain_image_path)
    brain_img_html = f"data:image/png;base64,{brain_b64}"
else:
    brain_img_html = ""

# Custom styling block
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&family=Quicksand:wght@500;600;700&display=swap');

.stApp {
    background: radial-gradient(circle at top center, #1e1c2e, #11131c) !important;
    color: #F3F4F6 !important;
    font-family: 'Nunito', sans-serif;
}

[data-testid="stHeader"] {
    background-color: transparent !important;
}

[data-testid="stSidebar"] {
    background-color: rgba(30, 33, 48, 0.95) !important;
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(167, 139, 250, 0.2) !important;
}

h1, h2, h3, h4, h5, h6, .brand-title {
    font-family: 'Quicksand', sans-serif !important;
    font-weight: 700;
}

p, label, button, input, textarea, li {
    font-family: 'Nunito', sans-serif !important;
}

.interactive-brain {
    transition: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
    filter: drop-shadow(0 0 15px rgba(167, 139, 250, 0.3));
    cursor: pointer;
    animation: float 6s ease-in-out infinite;
}
.interactive-brain:hover {
    transform: scale(1.05) rotate(2deg);
    filter: drop-shadow(0 0 35px rgba(167, 139, 250, 0.7)) brightness(1.1);
}

@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-15px); }
    100% { transform: translateY(0px); }
}

.glass-card {
    background: rgba(37, 42, 61, 0.5);
    backdrop-filter: blur(12px);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 30px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.glass-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    border-top: 2px solid #A78BFA;
}

.splash-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 80vh;
    animation: fadeInOut 4s ease-in-out;
}
.splash-image {
    width: 320px;
    height: auto;
    border-radius: 50%;
    animation: pulseGlow 2.5s infinite alternate;
}
@keyframes pulseGlow {
    from { box-shadow: 0 0 30px rgba(167, 139, 250, 0.3); transform: scale(0.98); }
    to { box-shadow: 0 0 70px rgba(167, 139, 250, 0.8); transform: scale(1.03); }
}
@keyframes fadeInOut {
    0% { opacity: 0; transform: scale(0.9); }
    15% { opacity: 1; transform: scale(1); }
    85% { opacity: 1; transform: scale(1); }
    100% { opacity: 0; transform: scale(1.1); }
}

div[data-baseweb="input"] {
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

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
    escaped = html.escape(text)
    escaped = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped)
    escaped = re.sub(r'__(.*?)__', r'<strong>\1</strong>', escaped)
    escaped = re.sub(r'\*(.*?)\*', r'<em>\1</em>', escaped)
    escaped = re.sub(r'_(.*?)_', r'<em>\1</em>', escaped)
    lines = escaped.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('- '):
            lines[i] = f"• {stripped[2:]}"
        elif stripped.startswith('* '):
            lines[i] = f"• {stripped[2:]}"
    escaped = '\n'.join(lines)
    escaped = escaped.replace('\n', '<br>')
    return escaped

# Session State Initialization
if "app_page" not in st.session_state:
    st.session_state.app_page = "intro"
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
if "skipped_tips" not in st.session_state:
    st.session_state.skipped_tips = []
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ==========================================
# PAGE ROUTING FUNCTIONS
# ==========================================

def show_intro():
    st.markdown(f"""
    <div class="splash-container">
        <img src="{brain_img_html}" class="splash-image" alt="MindSpace Brain" />
        <h2 style="color: #A78BFA; font-family: 'Quicksand', sans-serif; font-size: 1.8rem; margin-top: 30px; font-weight: 600; letter-spacing: 1.5px; text-shadow: 0 0 15px rgba(167, 139, 250, 0.4); text-align: center;">
            Your Personal<br>AI Mental Health Buddy
        </h2>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(4)
    st.session_state.app_page = "home"
    st.rerun()

def show_home():
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.2, 1], gap="large")
    
    with col1:
        st.markdown("""
        <h1 style='font-size: 3.8rem; color: #E5E7EB; margin-bottom: 5px; line-height: 1.1;'>Find Your<br><span style='color: #A78BFA;'>MindSpace</span></h1>
        <p style='font-size: 1.15rem; color: #94A3B8; margin-bottom: 30px; margin-top: 15px; line-height: 1.6;'>
            A safe, judgment-free AI companion designed with psychology in mind to help you navigate stress, anxiety, and the challenges of student life.
        </p>
        """, unsafe_allow_html=True)
        
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 0.5])
        with btn_col1:
            if st.button("Log In", use_container_width=True, type="primary"):
                st.session_state.app_page = "login"
                st.rerun()
        with btn_col2:
            if st.button("Sign Up", use_container_width=True):
                st.session_state.app_page = "signup"
                st.rerun()
                
    with col2:
        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
            <img src="{brain_img_html}" class="interactive-brain" style="width: 100%; max-width: 350px; border-radius: 50%;" />
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
    <div style='display: flex; justify-content: space-between; gap: 20px; margin-top: 80px; flex-wrap: wrap;'>
        <div class='glass-card' style='flex: 1; min-width: 200px;'>
            <h3 style='color: #34D399; margin-top: 0;'>Listen 🌿</h3>
            <p style='font-size: 15px; color: #E5E7EB; line-height: 1.6;'>Always here to listen to your thoughts without judgment, 24/7.</p>
        </div>
        <div class='glass-card' style='flex: 1; min-width: 200px;'>
            <h3 style='color: #F59E0B; margin-top: 0;'>Understand 🧠</h3>
            <p style='font-size: 15px; color: #E5E7EB; line-height: 1.6;'>Detects your mood intelligently and adapts its responses to support you best.</p>
        </div>
        <div class='glass-card' style='flex: 1; min-width: 200px;'>
            <h3 style='color: #60A5FA; margin-top: 0;'>Guide 🧭</h3>
            <p style='font-size: 15px; color: #E5E7EB; line-height: 1.6;'>Provides quick relief exercises like guided box breathing and journaling.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_login():
    st.markdown("<h2 style='text-align: center; color: #A78BFA; margin-top: 50px; font-size: 2.5rem;'>Welcome Back</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 40px;'>Log in to continue your journey.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        username_or_email = st.text_input("Username or Email", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Submit Login", use_container_width=True, type="primary"):
            if username_or_email and password:
                user = get_user_by_username(username_or_email) or get_user_by_email(username_or_email)
                if user:
                    if user['auth_provider'] != 'manual':
                        st.error(f"This account uses Google Login. Please use 'Sign in with Google'.")
                    elif not user['is_verified']:
                        st.error("Please verify your email first.")
                    else:
                        if verify_password(password, user['password_hash']):
                            st.session_state.current_user = user
                            if not user.get('onboarding_completed', False):
                                st.session_state.app_page = "onboarding"
                            else:
                                st.session_state.app_page = "chatbot"
                            st.rerun()
                        else:
                            st.error("Invalid credentials.")
                else:
                    st.error("Invalid credentials.")
            else:
                st.error("Please enter both username/email and password.")
        
        st.markdown("<hr style='border-color: rgba(167, 139, 250, 0.2); margin: 30px 0;'>", unsafe_allow_html=True)
        st.markdown(get_google_button_html(), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Back to Home", use_container_width=True):
            st.session_state.app_page = "home"
            st.rerun()

def show_signup():
    st.markdown("<h2 style='text-align: center; color: #A78BFA; margin-top: 50px; font-size: 2.5rem;'>Create an Account</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 40px;'>Join MindSpace to start focusing on your well-being.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        username = st.text_input("Choose Username", placeholder="e.g. mindful_student")
        email = st.text_input("Email Address", placeholder="you@university.edu")
        password = st.text_input("Create Password", type="password", placeholder="Strong password")
        
        if password:
            is_strong, msg = check_password_strength(password)
            if is_strong:
                st.success("Strong password! ✨")
            else:
                st.warning(f"Weak Password: {msg}")
                
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Create Account", use_container_width=True, type="primary"):
            if not username or not email or not password:
                st.error("Please fill all fields to create an account.")
            elif not is_valid_email(email):
                st.error("Please enter a valid email address.")
            else:
                is_strong, msg = check_password_strength(password)
                if not is_strong:
                    st.error(f"Cannot proceed: {msg}")
                else:
                    if get_user_by_username(username):
                        st.error("Username is already taken.")
                    elif get_user_by_email(email):
                        st.error("Email is already registered.")
                    else:
                        hashed = hash_password(password)
                        if create_user(username, email, hashed, auth_provider='manual', is_verified=False):
                            code = generate_verification_code()
                            st.session_state.verification_code = code
                            st.session_state.verifying_username = username
                            st.session_state.verifying_email = email
                            
                            with st.spinner("Sending verification email..."):
                                send_verification_email(email, code)
                                
                            st.session_state.app_page = "verify"
                            st.rerun()
                        else:
                            st.error("A database error occurred.")
                
        st.markdown("<hr style='border-color: rgba(167, 139, 250, 0.2); margin: 30px 0;'>", unsafe_allow_html=True)
        st.markdown(get_google_button_html(), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Back to Home", use_container_width=True):
            st.session_state.app_page = "home"
            st.rerun()

def show_verify():
    st.markdown("<h2 style='text-align: center; color: #A78BFA; margin-top: 50px;'>Verify Your Email</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #94A3B8;'>We sent a 6-digit code to <strong>{st.session_state.get('verifying_email', 'your email')}</strong>.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        entered_code = st.text_input("6-Digit Code", max_chars=6)
        if st.button("Verify & Login", use_container_width=True, type="primary"):
            if entered_code == st.session_state.get("verification_code"):
                username = st.session_state.get("verifying_username")
                verify_user(username)
                user = get_user_by_username(username)
                st.session_state.current_user = user
                st.success("Email verified successfully!")
                time.sleep(1)
                if not user.get('onboarding_completed', False):
                    st.session_state.app_page = "onboarding"
                else:
                    st.session_state.app_page = "chatbot"
                st.rerun()
            else:
                st.error("Invalid verification code. Please try again.")

def show_onboarding():
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 1

    st.markdown("<h2 style='text-align: center; color: #A78BFA; margin-top: 50px; font-size: 2.5rem;'>Let's Get to Know You</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2.5, 1])
    with col2:
        if st.session_state.onboarding_step == 1:
            st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 30px;'>Step 1 of 3: The Basics</p>", unsafe_allow_html=True)
            dob = st.date_input("When is your Birthday?", min_value=datetime.date(1950, 1, 1), max_value=datetime.date.today(), value=datetime.date(2005, 1, 1))
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Next Step ➔", use_container_width=True, type="primary"):
                st.session_state.temp_dob = str(dob)
                st.session_state.onboarding_step = 2
                st.rerun()
                
        elif st.session_state.onboarding_step == 2:
            st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 30px;'>Step 2 of 3: Your Academic Life</p>", unsafe_allow_html=True)
            career_level = st.selectbox("What is your current level?", ["School", "Undergraduate (UG)", "Postgraduate (PG)", "Professional", "Other"])
            study_what = st.text_input("What are you studying or working on?", placeholder="e.g. B.Tech Computer Science")
            study_where = st.text_input("Where are you studying or working?", placeholder="e.g. Massachusetts Institute of Technology")
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("⬅ Back", use_container_width=True):
                    st.session_state.onboarding_step = 1
                    st.rerun()
            with col_b2:
                if st.button("Next Step ➔", use_container_width=True, type="primary"):
                    st.session_state.temp_career_level = career_level
                    if study_what and study_where:
                        st.session_state.temp_study_info = f"{study_what} at {study_where}"
                    elif study_what:
                        st.session_state.temp_study_info = study_what
                    elif study_where:
                        st.session_state.temp_study_info = study_where
                    else:
                        st.session_state.temp_study_info = "Not specified"
                        
                    st.session_state.onboarding_step = 3
                    st.rerun()
                    
        elif st.session_state.onboarding_step == 3:
            st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 20px;'>Step 3 of 3: Welcome</p>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background-color: rgba(37, 42, 61, 0.5); padding: 35px; border-radius: 15px; border: 1px solid rgba(167, 139, 250, 0.3); text-align: center;">
                <h3 style="color: #F3F4F6; font-size: 1.8rem; margin-top: 0;">Welcome to MindSpace! 🌿</h3>
                <p style="color: #E5E7EB; line-height: 1.8; margin-bottom: 25px; font-size: 1.1rem;">
                    We believe that mental well-being is the foundation of a successful life. MindSpace is built to be your trusted, confidential, and judgment-free companion. Here, your thoughts are safe, your feelings are valid, and support is always just a message away.
                </p>
                <p style="color: #A78BFA; font-weight: 600; font-size: 1.15rem;">You are never alone on this journey.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("⬅ Back", use_container_width=True):
                    st.session_state.onboarding_step = 2
                    st.rerun()
            with col_b2:
                if st.button("Get Started ✨", use_container_width=True, type="primary"):
                    update_user_onboarding(
                        st.session_state.current_user["username"], 
                        st.session_state.get("temp_dob", ""), 
                        st.session_state.get("temp_study_info", ""), 
                        st.session_state.get("temp_career_level", "")
                    )
                    # Refresh user object to show correct display name and status
                    st.session_state.current_user = get_user_by_username(st.session_state.current_user["username"])
                    st.session_state.app_page = "chatbot"
                    st.rerun()

def show_chatbot():
    # Only allow access if logged in
    if not st.session_state.current_user:
        st.warning("Please log in first.")
        st.session_state.app_page = "login"
        st.rerun()

    username = st.session_state.current_user["username"]

    if "messages" not in st.session_state:
        db_msgs = get_user_messages(username)
        if db_msgs:
            st.session_state.messages = db_msgs
        else:
            st.session_state.messages = [{"role": "assistant", "content": f"Hello {st.session_state.current_user['display_name']}! I'm MindSpace, your companion. How are you feeling today?", "show_tip": False, "tip_mood": "neutral"}]

    if "current_mood" not in st.session_state:
        st.session_state.current_mood = "neutral"

    if "mood_history" not in st.session_state:
        db_moods = get_user_moods(username)
        if db_moods:
            st.session_state.mood_history = db_moods
        else:
            st.session_state.mood_history = []

    with st.sidebar:
        st.markdown(f"<h3 style='color: #F3F4F6;'>Hello, {st.session_state.current_user.get('display_name', 'User')} 👋</h3>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: rgba(167, 139, 250, 0.2);'>", unsafe_allow_html=True)
        
        st.markdown("<h4 style='color: #A78BFA;'>Your MindSpace</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94A3B8; font-size: 0.9rem;'>I'm here to listen, support, and help you navigate your thoughts.</p>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            delete_user_history(username)
            st.session_state.messages = [{"role": "assistant", "content": f"Hello {st.session_state.current_user['display_name']}! I've wiped our history. We're starting fresh. How are you feeling today?", "show_tip": False, "tip_mood": "neutral"}]
            st.session_state.mood_history = []
            st.session_state.current_mood = "neutral"
            st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)        
        st.markdown("<h3 style='color: #A78BFA; font-size: 18px; margin-bottom: 10px;'>📈 Mood Timeline</h3>", unsafe_allow_html=True)
        if st.session_state.mood_history:
            trail_parts = []
            last_moods = st.session_state.mood_history[-6:]
            for m in last_moods:
                mood_val = m if isinstance(m, str) else m["mood"]
                meta = MOOD_METADATA.get(mood_val, MOOD_METADATA["neutral"])
                trail_parts.append(f"{meta['emoji']} {meta['label']}")
            trail_str = " → ".join(trail_parts)
            st.markdown(
                f"<div style='font-size: 13px; color: #E5E7EB; background-color: rgba(28, 31, 46, 0.5); "
                f"padding: 12px; border-radius: 12px; border: 1px solid rgba(167, 139, 250, 0.2); "
                f"line-height: 1.6; word-break: break-word;'>"
                f"{trail_str}"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown("<p style='font-size: 13px; color: #94A3B8; font-style: italic;'>No moods recorded yet. Start chatting!</p>", unsafe_allow_html=True)
            
        st.markdown("<hr style='border: 1px solid rgba(167, 139, 250, 0.2);'>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='color: #A78BFA; font-size: 18px; margin-bottom: 10px;'>⚡ Quick Relief</h3>", unsafe_allow_html=True)
        
        if st.button("💨 Box Breathing", use_container_width=True):
            st.session_state.messages.append({"role": "assistant", "content": f"### 💨 Quick Box Breathing\n{TIPS['anxious']['content']}", "show_tip": False, "tip_mood": "anxious"})
            st.rerun()
            
        if st.button("🧘 Grounding Exercise", use_container_width=True):
            st.session_state.messages.append({"role": "assistant", "content": f"### 🧘 Quick 5-4-3-2-1 Grounding\n{TIPS['stressed']['content']}", "show_tip": False, "tip_mood": "stressed"})
            st.rerun()
            
        if st.button("📝 Journaling Prompt", use_container_width=True):
            st.session_state.messages.append({"role": "assistant", "content": f"### 📝 Quick Gratitude Journaling\n{TIPS['sad']['content']}", "show_tip": False, "tip_mood": "sad"})
            st.rerun()
            
        st.markdown("<hr style='border: 1px solid rgba(167, 139, 250, 0.2);'>", unsafe_allow_html=True)
        
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.app_page = "home"
            st.rerun()

    # MAIN CHAT
    st.markdown("<h1 style='margin-top: 0; color: #A78BFA; font-size: 2.8rem;'>🌿 MindSpace</h1>", unsafe_allow_html=True)
    
    if st.session_state.get('crisis_triggered', False):
        st.markdown(CRISIS_BANNER_HTML, unsafe_allow_html=True)
    
    current_mood_data = st.session_state.current_mood
    mood_val = current_mood_data["mood"] if isinstance(current_mood_data, dict) else current_mood_data
    intensity = current_mood_data["intensity"] if isinstance(current_mood_data, dict) else "medium"
    meta = MOOD_METADATA.get(mood_val, MOOD_METADATA["neutral"])
    intensity_label = intensity.upper()
    
    badge_html = f"""
    <div style="
        display: inline-flex;
        align-items: center;
        background-color: {meta['color']}1A;
        border: 1px solid {meta['color']};
        color: {meta['color']};
        padding: 8px 16px;
        border-radius: 30px;
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 20px;
    ">
        <span style="margin-right: 8px; font-size: 16px;">{meta['emoji']}</span>
        Current State: {meta['label']} ({intensity_label})
    </div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)
    
    st.markdown("<p style='font-size: 13px; color: #94A3B8; margin-bottom: 8px; font-weight: 600;'>How are you feeling right now?</p>", unsafe_allow_html=True)
    mood_cols = st.columns(len(MOOD_METADATA))
    for col, (mood_key, m_meta) in zip(mood_cols, MOOD_METADATA.items()):
        with col:
            if st.button(m_meta["emoji"], key=f"mood_select_btn_{mood_key}", help=f"I'm feeling {m_meta['label']}", use_container_width=True):
                st.session_state.current_mood = {"mood": mood_key, "intensity": "medium"}
                st.session_state.mood_history.append({"mood": mood_key, "intensity": "medium"})
                save_mood(username, {"mood": mood_key, "intensity": "medium"})
                st.rerun()
    
    chat_placeholder = st.container()
    with chat_placeholder:
        for idx, msg in enumerate(st.session_state.messages):
            role = msg["role"]
            content_html = markdown_to_html(msg["content"])
            
            if role == "user":
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; width: 100%; margin: 15px 0;">
                    <div style="
                        background-color: rgba(167, 139, 250, 0.2);
                        color: #F5F3FF;
                        padding: 14px 20px;
                        border-radius: 20px 20px 4px 20px;
                        border: 1px solid rgba(167, 139, 250, 0.4);
                        max-width: 80%;
                        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                        font-size: 15.5px;
                        line-height: 1.6;
                    ">
                        {content_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; width: 100%; margin: 15px 0;">
                    <div style="
                        background-color: rgba(37, 42, 61, 0.7);
                        backdrop-filter: blur(10px);
                        color: #E5E7EB;
                        padding: 14px 20px;
                        border-radius: 20px 20px 20px 4px;
                        border-left: 4px solid #A78BFA;
                        max-width: 80%;
                        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
                        font-size: 15.5px;
                        line-height: 1.6;
                    ">
                        {content_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if msg.get("show_tip") and msg.get("tip_mood") in TIPS:
                    tip_mood = msg.get("tip_mood")
                    tip = TIPS[tip_mood]
                    tip_content_html = markdown_to_html(tip["content"])
                    
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; width: 100%; margin: -6px 0 10px 0;">
                        <details open style="
                            background-color: rgba(37, 42, 61, 0.7);
                            border: 1px solid rgba(167, 139, 250, 0.5);
                            border-radius: 12px;
                            padding: 14px 18px;
                            width: 80%;
                            color: #E5E7EB;
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        ">
                            <summary style="font-weight: 700; cursor: pointer; color: #A78BFA; outline: none; display: flex; align-items: center;">
                                💡 Recommended Exercise
                            </summary>
                            <div style="margin-top: 12px; font-size: 15px; line-height: 1.6; border-top: 1px solid rgba(167, 139, 250, 0.2); padding-top: 12px;">
                                <strong style="font-size: 16px; color: #F3F4F6;">{tip['title']}</strong>
                                <p style="margin: 6px 0 12px 0; color: #94A3B8; font-style: italic;">{tip['description']}</p>
                                {tip_content_html}
                            </div>
                        </details>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    fb_col1, fb_col2, fb_col3 = st.columns([2, 2, 3])
                    with fb_col1:
                        if msg.get("feedback_given") == "helpful":
                            st.markdown("<p style='color: #34D399; font-size: 14px; font-weight: 700; margin-top: 8px;'>Glad that helped! 💜</p>", unsafe_allow_html=True)
                        elif msg.get("feedback_given") == "try_another":
                            pass
                        else:
                            if st.button("👍 This helps", key=f"help_btn_{idx}"):
                                msg["feedback_given"] = "helpful"
                                st.rerun()
                    with fb_col2:
                        if not msg.get("feedback_given"):
                            if st.button("🔄 Try Another", key=f"try_another_btn_{idx}"):
                                all_tip_keys = list(TIPS.keys())
                                if "skipped_tips" not in st.session_state:
                                    st.session_state.skipped_tips = []
                                if tip_mood not in st.session_state.skipped_tips:
                                    st.session_state.skipped_tips.append(tip_mood)
                                remaining = [k for k in all_tip_keys if k not in st.session_state.skipped_tips]
                                if not remaining:
                                    st.session_state.skipped_tips = [tip_mood]
                                    remaining = [k for k in all_tip_keys if k != tip_mood]
                                next_mood = remaining[0] if remaining else tip_mood
                                msg["tip_mood"] = next_mood
                                st.rerun()
    
    if user_input := st.chat_input("Share your thoughts..."):
        # Add user message to state and DB
        st.session_state.messages.append({"role": "user", "content": user_input})
        save_message(username, "user", user_input)
        
        # Determine mood
        detected = detect_mood(st.session_state.messages)
        st.session_state.current_mood = detected
        st.session_state.mood_history.append(detected)
        
        mood_str = detected["mood"] if isinstance(detected, dict) else str(detected)
        save_mood(username, mood_str)
        
        with st.spinner("MindSpace is thinking..."):
            ai_reply = get_chat_response(
                st.session_state.messages,
                user_data=st.session_state.current_user
            )
            
        negative_moods = ["anxious", "sad", "stressed", "lonely", "overwhelmed"]
        show_tip = False
        if detected["mood"] in negative_moods and detected["intensity"] in ["medium", "high"]:
            show_tip = True
         # Add bot message to state and DB
        st.session_state.messages.append({
            "role": "assistant",
            "content": ai_reply,
            "show_tip": show_tip,
            "tip_mood": detected["mood"]
        })
        save_message(username, "assistant", ai_reply)
        st.rerun()

# ==========================================
# MAIN EXECUTION
# ==========================================
if st.session_state.app_page == "intro":
    show_intro()
elif st.session_state.app_page == "home":
    show_home()
elif st.session_state.app_page == "login":
    show_login()
elif st.session_state.app_page == "signup":
    show_signup()
elif st.session_state.app_page == "verify":
    show_verify()
elif st.session_state.app_page == "onboarding":
    show_onboarding()
elif st.session_state.app_page == "chatbot":
    show_chatbot()
