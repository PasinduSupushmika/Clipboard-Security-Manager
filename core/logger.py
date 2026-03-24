"""
Encrypted rolling log system.
Logs are AES-256-GCM encrypted JSON lines stored in ~/.csm/logs/YYYY-MM-DD.log.enc
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.config import LOGS_DIR, LOG_RETENTION_DAYS
from core.crypto import encrypt, decrypt


class Logger:
    def __init__(self, key: bytes):
        self._key = key
        self._purge_old_logs()

    # ------------------------------------------------------------------
    def _today_file(self) -> Path:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return LOGS_DIR / f"{date_str}.log.enc"

    def _purge_old_logs(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=LOG_RETENTION_DAYS)
        for f in LOGS_DIR.glob("*.log.enc"):
            try:
                file_date = datetime.strptime(f.stem.replace(".log", ""), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if file_date < cutoff:
                    f.unlink()
            except ValueError:
                pass  # Skip files with unexpected names

    # ------------------------------------------------------------------
    def log(self, event_type: str, detail: str) -> None:
        """Append an encrypted log entry for today."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "detail": detail,
        }
        line = json.dumps(entry)
        encrypted_line = encrypt(line, self._key)

        log_file = self._today_file()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(encrypted_line + "\n")

    # ------------------------------------------------------------------
    def read_today(self) -> list[dict]:
        """Decrypt and return today's log entries."""
        log_file = self._today_file()
        if not log_file.exists():
            return []
        entries = []
        for line in log_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    plain = decrypt(line, self._key)
                    entries.append(json.loads(plain))
                except Exception:
                    entries.append({"ts": "?", "event": "UNREADABLE", "detail": line})
        return entries

    def read_all(self) -> list[dict]:
        """Decrypt and return all log entries across all retained days."""
        all_entries = []
        for log_file in sorted(LOGS_DIR.glob("*.log.enc")):
            for line in log_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    try:
                        plain = decrypt(line, self._key)
                        all_entries.append(json.loads(plain))
                    except Exception:
                        all_entries.append({"ts": "?", "event": "UNREADABLE", "detail": line})
        return all_entries
