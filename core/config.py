import os
from pathlib import Path

import sys

# Base directory for storing application data
USER_HOME = Path.home()
CSM_DATA_DIR = USER_HOME / ".csm"
CSM_DB_PATH = CSM_DATA_DIR / "csm_database.sqlite3"

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Lockout and retention policies
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes
MAX_LOGIN_ATTEMPTS = 3
LOG_RETENTION_DAYS = 30

# ==============================================================================
# EMAIL SERVICE CONFIGURATION (DUMMY DATA FOR GMAIL)
# ==============================================================================
# REPLACE_ME: Configure your Gmail SMTP settings here or via the UI setup wizard.
# If using Gmail, you MUST enable 2-Step Verification and generate an "App Password"
# Use the generated App Password as the CSM_SMTP_PASSWORD.
# ==============================================================================

CSM_SMTP_HOST = "smtp.gmail.com"
CSM_SMTP_PORT = 587

# REPLACE_ME: Replace with your actual Gmail address (e.g., your.name@gmail.com)
CSM_SMTP_USER_EMAIL = "pasindusupushmika17@gmail.com"

# REPLACE_ME: Replace with your Gmail App Password
# NOTE: This is NOT your standard Gmail login password!
CSM_SMTP_APP_PASSWORD = "ABCD EFGH IJKL MNOP".replace(" ", "")

# REPLACE_ME: Who should receive the security alerts? (Can be the same as sender)
CSM_ALERT_RECEIVER_EMAIL = "pasindusupushmika17@gmail.com"

# ==============================================================================


def ensure_data_dir_exists():
    """Ensure the ~/.csm directory exists on startup."""
    CSM_DATA_DIR.mkdir(parents=True, exist_ok=True)
