# 🔒 Clipboard Security Manager (CSM)

[![Python Support](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/Release-v1.0.0-green.svg)](https://github.com/PasinduSupushmika/Clipboard-Security-Manager)

**Developed by iMazK pvt ltd**  
*Enterprise-Grade Clipboard Encryption Utility preventing unauthorized memory leakage of sensitive passwords, intellectual properties, and communication.*

In modern environments, applications often scrape the OS clipboard in the background natively. CSM operates as an interactive daemon hooking into `<ctrl>+C`/`<ctrl>+V` pipelines to dynamically execute AES-256-GCM encryption on the data itself holding the plaintext in isolated python memory rather than upon the OS memory.

---

## 🛠️ Key Features

- **Military-Grade Encryption:** Transparently secures text natively inside Python memory using `cryptography` AES-GCM implementations.
- **DPAPI OS Bindings:** Master passwords and session keys are secured using `Argon2` bounds safely inside the host OS Keyrings natively—preventing SQL dumps from breaking vaults.
- **OTP Recovery Architectures:** Completely supports remote OTP (One-Time-Password) recoveries routed to Google Mail domains verifying ownership prior to Master Key overrides.
- **Aggressive Uninstaller:** Total dependency destruction dynamically wiping Keyring payloads alongside leftover hard-drive installations mimicking enterprise deployments seamlessly.
- **Visual Footprinting Placeholder:** Unauthenticated users attempting to paste via Context Menus without providing a valid vault password exclusively dump a clean warning message rather than bleeding your raw password hashes into documents!

## 🚀 Installation & Deployment

CSM is packaged seamlessly via PyInstaller offering a dummy-proof `CSM Setup.exe` enterprise installation utilizing CustomTkinter UIs mirroring commercial setups.

### Running from Source
If utilizing raw python endpoints without compilation:
```bash
# Clone the repository natively
git clone https://github.com/PasinduSupushmika/Clipboard-Security-Manager.git

# Move into source
cd "Clipboard Security Manager"

# Load prerequisites 
pip install -r requirements.txt

# Start Daemon
python main.py
```

---

## 🏗️ Architecture Stack
* **Language**: `Python 3.14+`
* **UI**: `CustomTkinter`
* **Cryptography**: `Python-Cryptography` (AES-256), `Argon2`
* **Background Listeners**: `pynput` & `pystray`
* **Data Management**: `sqlite3`

## 📧 Support
For production queries, deployments, or custom corporate builds please consult the associated `ReadMe.txt` outputted inside the final distributions!

**iMazK pvt ltd**
> Contact: +94 702518774
> Support: pasindusupushmika17@gmail.com
