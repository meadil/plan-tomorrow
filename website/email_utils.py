import os
import resend
from flask import url_for, current_app
from itsdangerous import URLSafeTimedSerializer

# Generate a secure timed token for email verification
def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm-salt')

# Confirm token and return email if valid (< 24 hours old)
def confirm_verification_token(token, expiration=86400):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirm-salt', max_age=expiration)
        return email
    except Exception:
        return None

# Send Verification Email via Resend
def send_verification_email(user_email, token):
    resend.api_key = os.getenv("RESEND_API_KEY")
    
    verification_url = url_for('auth.verify_email', token=token, _external=True)

    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px; border: 1px solid #e5e8eb; border-radius: 16px;">
        <h2 style="color: #000000; font-size: 20px; font-weight: 700; margin-bottom: 8px;">Verify your email</h2>
        <p style="color: #50545c; font-size: 15px; line-height: 1.5;">Welcome to <strong>Plan Tomorrow</strong>! Click the button below to verify your email address and start organizing your day.</p>
        <a href="{verification_url}" style="display: inline-block; background-color: #000000; color: #ffffff; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 14px; margin-top: 16px; margin-bottom: 16px;">Verify Email Address</a>
        <p style="color: #8a8d98; font-size: 12px; margin-top: 20px;">If you didn't create an account, you can safely ignore this email.</p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": "Plan Tomorrow <onboarding@resend.dev>",
            "to": user_email,
            "subject": "Verify your Plan Tomorrow account",
            "html": html_content
        })
    except Exception as e:
        print(f"Failed to send email via Resend: {e}")