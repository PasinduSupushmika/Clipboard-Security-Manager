import os
from pathlib import Path

import sys

# Base directory for storing application data
USER_HOME = Path.home()
CSM_DATA_DIR = USER_HOME / ".csm"
CSM_DB_PATH = CSM_DATA_DIR / "csm_database.sqlite3"
LOGS_DIR = CSM_DATA_DIR / "logs"

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        # During dev, use the project root (one level up from core/)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)

# Lockout and retention policies
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes
MAX_LOGIN_ATTEMPTS = 3
LOG_RETENTION_DAYS = 30

# ==============================================================================
# EMAIL SERVICE CONFIGURATION
# ==============================================================================
# Gmail credentials are configured during setup wizard and stored securely
# in OS Keyring (DPAPI on Windows, Keychain on Mac, Secret Service on Linux)
# See: auth.set_gmail_credentials() and auth.get_gmail_credentials()
# ==============================================================================

CSM_SMTP_HOST = "smtp.gmail.com"
CSM_SMTP_PORT = 587

# NOTE: Credentials are no longer stored here - they are in OS Keyring!
# ==============================================================================


def ensure_data_dir_exists():
    """Ensure the ~/.csm and logs subdirectories exist on startup."""
    CSM_DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
