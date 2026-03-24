import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from . import config

def _send_email(subject: str, message_body: str, to_address: str):
    """
    Internal helper to send an email using the Gmail SMTP configuration.
    Raises standard exceptions if the host is unreachable or dummy credentials fail.
    """
    msg = MIMEMultipart()
    msg['From'] = config.CSM_SMTP_USER_EMAIL
    msg['To'] = to_address
    msg['Subject'] = subject
    
    msg.attach(MIMEText(message_body, 'plain'))

    # If the user has not replaced the dummy credentials, we skip sending with a print warning.
    if config.CSM_SMTP_APP_PASSWORD == "DUMMY_GMAIL_APP_PASSWORD" or config.CSM_SMTP_USER_EMAIL == "DUMMY_SENDER_EMAIL@gmail.com":
        print(f"[WARN] Dummy Gmail details found. Skipping email dispatch to {to_address} for: {subject}")
        # Not throwing exception here so testing local flows won't crash when internet is off/fake
        return False

    try:
        # Connect to Gmail SMTP (TLS)
        server = smtplib.SMTP(config.CSM_SMTP_HOST, config.CSM_SMTP_PORT)
        server.starttls()
        
        # Login using real credentials
        server.login(config.CSM_SMTP_USER_EMAIL, config.CSM_SMTP_APP_PASSWORD)
        
        # Dispatch the message
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to dispatch email via {config.CSM_SMTP_HOST}: {e}")
        return False

def send_alert_email(incident_details: str):
    """
    Triggered when an unauthorized attempt reaches the escalation threshold (e.g., 2nd or 3rd failed password).
    """
    subject = f"Security Alert: Clipboard Security Manager Incident"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    body = (
        f"An unauthorized clipboard decryption attempt was logged on your machine.\n\n"
        f"Timestamp: {timestamp}\n"
        f"Incident Details:\n{incident_details}\n\n"
        f"If this was not you, please ensure your workstation is secured."
    )

    # Deliver to the configured native keyring receiver email address dynamically
    from . import auth
    return _send_email(subject, body, auth.get_user_email())

def send_otp_email(otp_code: str, to_address: str):
    """
    Sends the One-Time-Password for the Master Password recovery workflow natively. 
    """
    subject = "CSM Master Password - Reset Request"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    body = (
        f"A master password reset was requested on {timestamp}.\n\n"
        f"Your One-Time Password (OTP) is:\n\n"
        f"      {otp_code}\n\n"
        f"This code will expire shortly. Do not share this code with anyone."
    )
    
    # Deliver OTP back to the provided address securely
    return _send_email(subject, body, to_address)
