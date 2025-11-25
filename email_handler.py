import smtplib
from email.message import EmailMessage
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Step 9. Set Up the Email System (Load credentials from .env)
SENDER_EMAIL = os.getenv("APP_EMAIL_USER")
SENDER_PASSWORD = os.getenv("APP_EMAIL_PASS")
SMTP_SERVER = "smtp.gmail.com" # Change this if you use a different service
SMTP_PORT = 587 # Standard TLS port

def send_final_email(recipient_email, officer_name, report_id, report_text, log_id):
    if not all([SENDER_EMAIL, SENDER_PASSWORD]):
        print("Email credentials missing in .env. Skipping email.")
        return 

    msg = EmailMessage()
    msg['Subject'] = f"FINALIZED Incident Report - ID: {report_id}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    
    email_body = f"""
    Dear Officer {officer_name},

    This is the FINALIZED version of Incident Report {report_id} that you affirmed.

    --------------------------------------------------
    {report_text}
    --------------------------------------------------

    Administrative Notes:
    - Final Audit Log ID: {log_id}
    - Sent Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    Please save this email for your records. This is an automated message.
    """
    msg.set_content(email_body)

    try:
        # Connect to the SMTP server (Step 9. Core action)
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # Secure the connection
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"Email successfully sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False