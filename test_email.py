import resend
import os

resend.api_key = os.getenv("RESEND_API_KEY")

params = {
    "from": "onboarding@resend.dev",
    "to": ["aitallalaya2335@gmail.com"],
    "subject": "Test email",
    "text": "Hello! This is a test from my predictive maintenance project."
}

try:
    email = resend.Emails.send(params)
    print("Email sent successfully!")
    print(email)
except Exception as e:
    print(f"Email sending failed: {e}")