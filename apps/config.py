"""
Simple config constants. Move to environment variables before any real deployment.
"""

ALERT_RECIPIENT_EMAIL = os.getenv("ALERT_RECIPIENT_EMAIL", "")  
CONFIDENCE_ALERT_THRESHOLD = 0.80