import os
import random
import re
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import keyring

from . import config
from . import email_service

# Argon2 is explicitly modeled for memory-hard, GPU-resistant password hashing 
ph = PasswordHasher()

# We need an ephemeral store for OTP validation
_CURRENT_OTP = None

# A constant service name to identify our symmetric AES Key in the OS secure storage (DPAPI/Keychain)
SERVICE_NAME = "ClipboardSecurityManager"
KEY_TAG = "AES_MASTER_KEY"
HASH_TAG = "MASTER_PASSWORD_HASH"
EMAIL_TAG = "USER_RECOVERY_EMAIL"

def validate_password_complexity(password: str) -> bool:
    """Verifies NIST/Enterprise standard 8-character symbol schemas dynamically."""
    if len(password) < 8: return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"[0-9]", password): return False
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password): return False
    return True

def validate_email_format(email: str) -> bool:
    """Hard-checks matching requested @gmail.com logic."""
    return email.strip().endswith("@gmail.com")

def is_setup_complete() -> bool:
    """Check if the master password has been established."""
    return keyring.get_password(SERVICE_NAME, HASH_TAG) is not None

def setup_master_password(password: str):
    """
    Called on initial run or via Dashboard.
    Hashes the user password using Argon2 and stores it securely in the OS Keyring.
    Also initializes a random 32-byte AES key for the background copy operations if one does not exist.
    """
    hashed = ph.hash(password)
    keyring.set_password(SERVICE_NAME, HASH_TAG, hashed)

    # Initialize symmetric background encryption key if first setup
    if keyring.get_password(SERVICE_NAME, KEY_TAG) is None:
        # Generate 32-Byte cryptographically secure key and store strictly natively in the OS keystore
        new_key = os.urandom(32).hex()
        keyring.set_password(SERVICE_NAME, KEY_TAG, new_key)

def verify_master_password(password: str) -> bool:
    """Verifies an attempted password against the Argon2 hash stored natively in the DB/Keyring."""
    stored_hash = keyring.get_password(SERVICE_NAME, HASH_TAG)
    if not stored_hash:
        return False
        
    try:
        ph.verify(stored_hash, password)
        # If verify succeeds without throwing VerifyMismatchError, password is valid.
        return True
    except VerifyMismatchError:
        return False

def save_user_email(email: str):
    """Binds the validated generic Email receiver dynamically into the OS keychain."""
    keyring.set_password(SERVICE_NAME, EMAIL_TAG, email.strip())

def get_user_email() -> str:
    """Retrieves the recipient safely without config file dependencies."""
    return keyring.get_password(SERVICE_NAME, EMAIL_TAG) or "Unknown"

def delete_all_credentials():
    """Wipes the physical Keychain data clean during UNINSTALL commands."""
    for tag in [HASH_TAG, KEY_TAG, EMAIL_TAG]:
        try:
            keyring.delete_password(SERVICE_NAME, tag)
        except:
            pass

def generate_and_send_recovery_otp(target_email: str = None) -> bool:
    """Generates a secure 6-digit OTP mapping it into ephemeral memory, and sends to the registered address."""
    global _CURRENT_OTP
    
    # 6 digit code
    _CURRENT_OTP = str(random.randint(100000, 999999))
    
    # Allows Setup_Wizard to parse explicit Email during testing phase, or defaults to keychain
    recv = target_email if target_email else get_user_email()
    return email_service.send_otp_email(_CURRENT_OTP, recv)

def reset_password_with_otp(otp: str, new_password: str) -> bool:
    """Verifies the ephemeral OTP and executes a hash override to restore access."""
    global _CURRENT_OTP
    
    if _CURRENT_OTP and otp == _CURRENT_OTP:
        # Process the newly requested Argon2 hash
        setup_master_password(new_password)
        # Flush the ephemeral token
        _CURRENT_OTP = None
        return True
        
    return False

def get_aes_runtime_key() -> bytes:
    """Retrieves the AES-256 binary key injected into the OS secure Enclave upon setup."""
    hex_key = keyring.get_password(SERVICE_NAME, KEY_TAG)
    if not hex_key:
        raise Exception("AES Initialization Token Not Found. Complete Setup Wizard First.")
    return bytes.fromhex(hex_key)
