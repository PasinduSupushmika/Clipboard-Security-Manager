import time
from . import config
from . import email_service
from . import database
from . import crypto

# Ephemeral Session States
_FAILED_ATTEMPTS = 0
_LOCKOUT_TIMESTAMP = 0

def record_attempt(success: bool) -> dict:
    """
    Maintains per-session counters.
    Returns a dictionary informing the caller UI if it should trigger a lockout or deny state.
    """
    global _FAILED_ATTEMPTS, _LOCKOUT_TIMESTAMP

    # Reset on valid auth
    if success:
        _FAILED_ATTEMPTS = 0
        return {"action": "ALLOW", "message": "Success"}

    # Increment failure and evaluate rules
    _FAILED_ATTEMPTS += 1
    
    # Use AES 256 GCM to secure precisely what occurred in the session
    try:
        engine = crypto.CryptoEngine(auth.get_aes_runtime_key())
    except:
        engine = None
    
    def _safe_encrypt(msg: str):
        if engine:
            return engine.encrypt(msg.encode('utf-8'))
        return msg.encode('utf-8') # Fallback to raw bytes if engine fails

    if _FAILED_ATTEMPTS == 1:
        database.insert_log("FAILED_AUTH_1", _safe_encrypt("First Invalid Password Attempt"))
        return {"action": "DENY", "retry": True, "message": "Invalid Password. Please try again."}
        
    elif _FAILED_ATTEMPTS == 2:
        database.insert_log("FAILED_AUTH_2", _safe_encrypt("Second Consecutive Invalid Attempt"))
        # Trigger an email alert immediately
        email_service.send_alert_email("Two consecutive failed master password attempts on CSM.", severity=2)
        return {"action": "DENY", "retry": True, "message": "Second Invalid Attempt. Security alert sent."}
        
    elif _FAILED_ATTEMPTS >= 3:
        database.insert_log("FAILED_AUTH_3_LOCKOUT", _safe_encrypt(f"System Lockout Protocol for 3 consecutive failures"))
        _LOCKOUT_TIMESTAMP = time.time()
        # Escalate into a full email lockout notification
        email_service.send_alert_email("Critical: Clipboard locked entirely due to 3 consecutive failed authorization requests.", severity=3)
        return {"action": "LOCKOUT", "retry": False, "message": f"Clipboard locked for {config.LOCKOUT_DURATION_SECONDS} seconds."}

def is_locked() -> bool:
    """Returns True if the user is actively locked out inside the 5-minute penalty window."""
    global _LOCKOUT_TIMESTAMP, _FAILED_ATTEMPTS
    
    if _LOCKOUT_TIMESTAMP == 0:
        return False
        
    time_passed = time.time() - _LOCKOUT_TIMESTAMP
    
    if time_passed >= config.LOCKOUT_DURATION_SECONDS:
        # Time expired naturally, unlock them gracefully
        _LOCKOUT_TIMESTAMP = 0
        _FAILED_ATTEMPTS = 0
        return False
        
    # Still serving penalty
    return True
