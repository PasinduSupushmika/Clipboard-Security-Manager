import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from . import config
from .config import resource_path

# Helper context values mapping the enterprise structure dynamically
COMMON_CONTEXT = {
    "{{CompanyName}}": "iMazK pvt ltd",
    "{{Year}}": str(datetime.now().year),
    "{{SupportEmail}}": "pasindusupushmika17@gmail.com",
    "{{PrivacyPolicyURL}}": "#"
}

def _load_template(template_name: str) -> str:
    """Safely retrieves the HTML layout provided by the user within the UI filesystem."""
    try:
        path = resource_path(os.path.join("Email Templates", template_name))
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[WARN] Failed to load {template_name}: {e}")
        return ""

def _send_email(subject: str, message_body: str, to_address: str, is_html: bool = True):
    msg = MIMEMultipart()
    msg['From'] = config.CSM_SMTP_USER_EMAIL
    msg['To'] = to_address
    msg['Subject'] = subject
    
    msg.attach(MIMEText(message_body, 'html' if is_html else 'plain'))

    if config.CSM_SMTP_APP_PASSWORD == "DUMMY_GMAIL_APP_PASSWORD" or config.CSM_SMTP_USER_EMAIL == "DUMMY_SENDER_EMAIL@gmail.com":
        print(f"[WARN] Dummy Gmail details found. Skipping email dispatch to {to_address} for: {subject}")
        return False

    try:
        server = smtplib.SMTP(config.CSM_SMTP_HOST, config.CSM_SMTP_PORT)
        server.starttls()
        server.login(config.CSM_SMTP_USER_EMAIL, config.CSM_SMTP_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to dispatch via {config.CSM_SMTP_HOST}: {e}")
        return False

def _apply_context(html: str, context: dict) -> str:
    """Loops over dict overriding template variables."""
    for key, val in COMMON_CONTEXT.items():
        html = html.replace(key, str(val))
    for key, val in context.items():
        html = html.replace(key, str(val))
    return html

def send_alert_email(incident_details: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"Security Alert: Clipboard Security Manager Incident"
    
    html = _load_template("email_incorrect_password.html")
    if not html:
        return False
        
    context = {
        "{{UserName}}": "Admin",
        "{{AttemptCount}}": "3+",
        "{{AttemptDateTime}}": timestamp,
        "{{IPAddress}}": "Current Workstation",
        "{{DeviceInfo}}": "Windows System",
        "{{Location}}": "Local Machine",
        "{{ResetPasswordURL}}": "#"
    }
    
    body = _apply_context(html, context)
    from . import auth
    return _send_email(subject, body, auth.get_user_email())

def send_otp_email(otp_code: str, to_address: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if this is a setup verification natively using the current keychain
    from . import auth
    if auth.get_user_email() == "Unknown" or not auth.is_setup_complete():
        subject = "CSM Setup - Verify Your Email Address"
        html = _load_template("email_setup_otp.html")
        context = {
            "{{UserName}}": "User",
            "{{OTPCode}}": otp_code,
            "{{OTPExpiry}}": "5"
        }
    else:
        subject = "CSM Master Password - Reset Request"
        html = _load_template("email_password_change_otp.html")
        context = {
            "{{UserName}}": "Admin",
            "{{OTPCode}}": otp_code,
            "{{OTPExpiry}}": "5",
            "{{RequestDateTime}}": timestamp,
            "{{IPAddress}}": "Current Workstation",
            "{{DeviceInfo}}": "Windows System"
        }
        
    if not html:
        return False
    
    body = _apply_context(html, context)
    return _send_email(subject, body, to_address)
