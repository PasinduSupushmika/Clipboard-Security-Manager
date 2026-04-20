#!/usr/bin/env python3
"""
encode_creds.py  –  XOR-encode company Gmail credentials for embedding in email_service.py

Usage:
    python3 tools/encode_creds.py  your_sender@gmail.com  YourAppPassword

Output:
    Paste the two printed byte arrays into email_service.py as _EA and _AP.
"""

import sys

_XK = 0x5A   # Must match _XK in email_service.py

def encode(text: str) -> str:
    data = bytes([ord(c) ^ _XK for c in text])
    hex_pairs = ", ".join(f"0x{b:02x}" for b in data)
    return f"bytes([{hex_pairs}])"

if len(sys.argv) != 3:
    print(__doc__)
    sys.exit(1)

email    = sys.argv[1].strip()
password = sys.argv[2].strip().replace(" ", "")

print("\n# ── Paste these two lines into core/email_service.py ──────────────")
print(f"_EA = {encode(email)}")
print(f"_AP = {encode(password)}")
print("# ────────────────────────────────────────────────────────────────────\n")
print(f"  Encodes: {email}")
print(f"  Encodes: {'*' * len(password)}  ({len(password)} chars)\n")
