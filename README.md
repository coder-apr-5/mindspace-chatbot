---
title: MindSpace Mental Health Companion
emoji: 🌿
colorFrom: purple
colorTo: blue
sdk: streamlit
sdk_version: 1.32.0
app_file: app.py
pinned: false
license: mit
---

# MindSpace — Student Mental Health Companion Chatbot

MindSpace is a compassionate, student-focused AI mental health companion chatbot built using **Streamlit** and powered by **Groq's LPU Inference Engine** using the `llama-3.3-70b-versatile` model.

*Note: MindSpace is designed as a companion tool and is not a substitute for professional mental health care.*

## Features
- **Real-time Mood Detection**: Instantly analyzes current user state to track transitions and display badges.
- **Empathetic AI Companion**: Guided by safe active listening, validation, and professional safety guardrails.
- **Matched Relaxation Tip Cards**: Shows inline strategies (e.g. Box Breathing, Grounding) for high/medium distress moods.
- **Mood History Timeline**: Visualizes the last 6 mood states dynamically in the sidebar.
- **Crisis Safety Net**: Monitors for key triggers and presents a persistent non-dismissible helpline banner.
- **Quick-Relief Actions**: Side panel triggers for box breathing, grounding, or journaling prompts.

---

## Local Development Setup

1. **Clone or Download** this directory.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables**:
   - Copy `.env.example` to a new file named `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and replace `your_groq_api_key_here` with your actual Groq API key from the [Groq Console](https://console.groq.com).
4. **Run the Streamlit application**:
   ```bash
   streamlit run app.py
   ```

---

## Deployment to Hugging Face Spaces

1. Create a new Space on [Hugging Face](https://huggingface.co/new-space).
2. Choose **Streamlit** as the SDK.
3. Upload all project files to the repository (either via git or the web UI).
4. Go to **Settings** -> **Variables and secrets** on your Hugging Face Space page.
5. Create a new Secret:
   - **Name**: `GROQ_API_KEY`
   - **Value**: Your Groq API key (e.g., `gsk_...`)
6. The Space will automatically build and deploy!
