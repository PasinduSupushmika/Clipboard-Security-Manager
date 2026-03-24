import sqlite3
import json
from datetime import datetime
from pathlib import Path
from . import config

def _get_connection():
    # Make sure the parent folder exists
    config.ensure_data_dir_exists()
    
    conn = sqlite3.connect(config.CSM_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the local SQLite database schema for logs and settings."""
    conn = _get_connection()
    c = conn.cursor()
    
    # Create Logs Table (Encrypted payloads are stored)
    c.execute('''
        CREATE TABLE IF NOT EXISTS Logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            encrypted_payload BLOB NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def insert_log(event_type: str, encrypted_payload: bytes):
    """
    Insert an encrypted event log into the database.
    Since clipboard contents and details might be sensitive, we want the logs AES-encrypted 
    before making their way here.
    """
    conn = _get_connection()
    c = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    c.execute(
        "INSERT INTO Logs (timestamp, event_type, encrypted_payload) VALUES (?, ?, ?)",
        (timestamp, event_type, encrypted_payload)
    )
    
    conn.commit()
    conn.close()

def get_recent_logs(limit: int = 100):
    """Fetch the latest event logs."""
    conn = _get_connection()
    c = conn.cursor()
    
    c.execute(
        "SELECT id, timestamp, event_type, encrypted_payload FROM Logs ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def purge_old_logs():
    """
    Removes database rows older than LOG_RETENTION_DAYS (30 days default).
    This implements the 30-day retention requirement from the SSS PDF.
    """
    conn = _get_connection()
    c = conn.cursor()
    
    retention_threshold = (
        datetime.now().date().toordinal() - config.LOG_RETENTION_DAYS
    )
    
    # We will compute the date from isoformat strictly, using python or sqlite date modifier.
    c.execute(
        "DELETE FROM Logs WHERE timestamp <= datetime('now', '-30 days')"
    )
    
    conn.commit()
    conn.close()
