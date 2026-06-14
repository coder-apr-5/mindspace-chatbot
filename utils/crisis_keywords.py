# Safety terms and Indian helplines for crisis safety net

CRISIS_KEYWORDS = [
    "suicide",
    "self-harm",
    "end my life",
    "kill myself",
    "can't go on",
    "want to die",
    "better off dead",
    "no reason to live",
    "cut myself"
]

def check_for_crisis(text: str) -> bool:
    """
    Checks if any of the crisis keywords are present in the text (case-insensitive).
    """
    if not text:
        return False
    
    cleaned_text = text.lower().strip()
    for keyword in CRISIS_KEYWORDS:
        if keyword in cleaned_text:
            return True
    return False

# CSS and HTML template for crisis banner
CRISIS_BANNER_HTML = """
<div style="
    background-color: #3D1515;
    border: 1px solid #F87171;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
    color: #FEE2E2;
    font-family: 'Inter', sans-serif;
">
    <div style="display: flex; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 20px; margin-right: 10px;">⚠️</span>
        <strong style="font-size: 16px; color: #FCA5A5;">Support is Available (Crisis Safety Net)</strong>
    </div>
    <p style="margin: 0 0 10px 0; font-size: 14px; line-height: 1.5;">
        If you are experiencing thoughts of self-harm or suicide, please know that you do not have to carry this alone. Please reach out to these free, confidential professional services:
    </p>
    <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6;">
        <li><strong>iCall (India)</strong>: <a href="tel:9152987821" style="color: #F87171; text-decoration: underline;">9152987821</a></li>
        <li><strong>Vandrevala Foundation</strong>: <a href="tel:18602662345" style="color: #F87171; text-decoration: underline;">1860-2662-345</a> (Available 24/7)</li>
    </ul>
    <p style="margin: 10px 0 0 0; font-size: 12px; color: #FCA5A5; font-style: italic;">
        MindSpace is an AI companion, not a replacement for professional healthcare. Please call the numbers above or contact a trusted person immediately.
    </p>
</div>
"""
