# =============================================================================
# core/email_service.py  –  Email dispatch engine
# =============================================================================
# Company Gmail credentials are embedded using XOR obfuscation (key 0x5A).
# No plaintext credential ever appears as a string literal in this file.
#
# TO SET YOUR REAL CREDENTIALS before building the EXE:
#   Run:  python3 tools/encode_creds.py  your@gmail.com  YourAppPassword
#   Then paste the printed _EA and _AP byte arrays below.
# =============================================================================

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from . import config
from .config import resource_path

# ---------------------------------------------------------------------------
# XOR mask – change this in encode_creds.py too if you rotate it
# ---------------------------------------------------------------------------
_XK = 0x5A

# ---------------------------------------------------------------------------
# Obfuscated company sender credentials
# These are XOR-obfuscated bytes (mask 0x5A).
# ---------------------------------------------------------------------------
_EA = bytes([
    
])  # Add Company email with encryption

_AP = bytes([
    
])  # Add Company emai app password with encryption


def _dx(data: bytes) -> str:
    """Decode XOR-obfuscated credential bytes at runtime only."""
    return "".join(chr(b ^ _XK) for b in data)


def _get_sender() -> tuple:
    """Return (sender_email, app_password) decoded from obfuscated bytes."""
    return _dx(_EA), _dx(_AP)


# ---------------------------------------------------------------------------
# Common template substitution values
# ---------------------------------------------------------------------------
COMMON_CONTEXT = {
    "{{CompanyName}}":      "iMazK pvt ltd",
    "{{Year}}":             str(datetime.now().year),
    "{{SupportEmail}}":     _dx(_EA),
    "{{PrivacyPolicyURL}}": "#",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _load_template(template_name: str) -> str:
    try:
        path = resource_path(os.path.join("Email Templates", template_name))
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[WARN] Template not found: {template_name} – {e}")
        return ""


def _apply_context(html: str, context: dict) -> str:
    for key, val in COMMON_CONTEXT.items():
        html = html.replace(key, str(val))
    for key, val in context.items():
        html = html.replace(key, str(val))
    return html


def _send_email(subject: str, body: str, to_address: str, is_html: bool = True) -> bool:
    """Send one email using the embedded company Gmail credentials."""
    sender_email, sender_password = _get_sender()

    if not sender_email or not sender_password:
        print("[ERROR] Company credentials not set – run tools/encode_creds.py first.")
        return False

    msg = MIMEMultipart()
    msg["From"]    = sender_email
    msg["To"]      = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html" if is_html else "plain"))

    try:
        srv = smtplib.SMTP(config.CSM_SMTP_HOST, config.CSM_SMTP_PORT)
        srv.starttls()
        srv.login(sender_email, sender_password)
        srv.send_message(msg)
        srv.quit()
        print(f"[INFO] Email dispatched -> {to_address}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("[ERROR] Gmail authentication failed – update _EA/_AP in email_service.py")
        return False
    except Exception as e:
        print(f"[ERROR] SMTP error: {e}")
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def send_otp_email(otp_code: str, to_address: str) -> bool:
    """
    Send a 6-digit OTP to the user's email.
    Picks the setup template on first run; the password-change template otherwise.
    """
    from . import auth
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if auth.get_user_email() == "Unknown" or not auth.is_setup_complete():
        subject  = "CSM Setup – Verify Your Email Address"
        template = "email_setup_otp.html"
        context  = {
            "{{UserName}}":   "User",
            "{{OTPCode}}":    otp_code,
            "{{OTPExpiry}}":  "5",
        }
    else:
        subject  = "CSM – Master Password Reset Request"
        template = "email_password_change_otp.html"
        context  = {
            "{{UserName}}":        "User",
            "{{OTPCode}}":         otp_code,
            "{{OTPExpiry}}":       "5",
            "{{RequestDateTime}}": timestamp,
            "{{IPAddress}}":       "Current Workstation",
            "{{DeviceInfo}}":      "Windows System",
        }

    html = _load_template(template)
    if not html:
        return False
    return _send_email(subject, _apply_context(html, context), to_address)


def send_alert_email(incident_details: str, severity: int = 3) -> bool:
    """
    Send a security alert to the user's registered email.
    Called automatically by escalation.py after 2+ failed paste attempts.
    """
    from . import auth

    user_email = auth.get_user_email()
    if user_email == "Unknown":
        print("[WARN] No user email stored – cannot send alert.")
        return False

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = (
        f"Security Alert: CSM Lockout ({severity}+ Attempts)"
        if severity >= 3
        else "Security Warning: CSM Invalid Attempts"
    )

    html = _load_template("email_incorrect_password.html")
    if not html:
        return False

    context = {
        "{{UserName}}":        "User",
        "{{AttemptCount}}":    f"{severity}+" if severity >= 3 else str(severity),
        "{{AttemptDateTime}}": timestamp,
        "{{IPAddress}}":       "Current Workstation",
        "{{DeviceInfo}}":      "Windows System",
        "{{Location}}":        "Local Machine",
        "{{ResetPasswordURL}}": "#",
    }
    return _send_email(subject, _apply_context(html, context), user_email)
