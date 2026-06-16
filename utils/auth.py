# pyrefly: ignore [missing-import]
import bcrypt
import re
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def check_password_strength(password: str):
    """
    Returns (is_strong, feedback_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    
    return True, "Strong password"

def is_valid_email(email: str) -> bool:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

def generate_verification_code() -> str:
    return str(random.randint(100000, 999999))

def send_verification_email(receiver_email: str, code: str) -> bool:
    sender_email = os.environ.get("SMTP_EMAIL")
    sender_password = os.environ.get("SMTP_APP_PASSWORD")
    
    if not sender_email or not sender_password:
        print("SMTP Credentials not configured in .env")
        # In a real app, returning False would block user if SMTP isn't set.
        # But for dev ease, if not set, we'll pretend it sent or print to console.
        print(f"DEV MODE: Verification code for {receiver_email} is {code}")
        return True # Fallback for local testing without SMTP

    msg = MIMEMultipart("alternative")
    msg['Subject'] = "MindSpace - Verify your Email"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    text = f"Your MindSpace verification code is: {code}"
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f4f5; padding: 20px; text-align: center;">
        <div style="background-color: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2 style="color: #A78BFA; font-family: serif;">🌿 MindSpace</h2>
            <p style="color: #3f3f46; font-size: 16px;">Hello,</p>
            <p style="color: #3f3f46; font-size: 16px;">Please use the following 6-digit code to verify your email address:</p>
            <div style="margin: 20px 0; padding: 15px; background-color: #f3f4f6; font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #1c1f2e; border-radius: 8px;">
                {code}
            </div>
            <p style="color: #71717a; font-size: 14px;">If you did not request this, please ignore this email.</p>
        </div>
      </body>
    </html>
    """

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
