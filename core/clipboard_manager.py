import time
import threading
import pyperclip
from pynput import keyboard

from . import crypto
from . import auth

# Replaces the raw Hash visual leak with a safe static placeholder
CSM_PLACEHOLDER = "[ CSM Encrypted Payload - Use Ctrl+V to authenticate ]"

class ClipboardMonitor:
    def __init__(self, paste_callback):
        """
        Initializes the dynamic clipboard monitor. 
        Requires passing a GUI UI callback for when a PASTE hook trigger activates.
        """
        self.running = False
        self.last_content = ""
        self.internal_cipher = None
        self.paste_callback = paste_callback
        
        # We initiate the cryptographic engine dynamically using our secure OS keyring 256-Bit Key
        try:
            self.engine = crypto.CryptoEngine(auth.get_aes_runtime_key())
        except Exception as e:
            print(f"[WARN] Engine Offline: {e}")
            self.engine = None

    def start_monitoring(self):
        """Spawns the continuous clipboard watcher thread safely."""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._poll_clipboard, daemon=True)
        self.monitor_thread.start()
        
        # Initiate the keyboard hook natively in a separate thread paradigm
        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+v': self._on_paste
        })
        self.listener.start()

    def stop_monitoring(self):
        self.running = False
        if hasattr(self, 'listener'):
            self.listener.stop()

    def _poll_clipboard(self):
        """Background daemon polling standard Win32 copy payloads enforcing cryptography transparently."""
        while self.running:
            try:
                current_clipboard = pyperclip.paste()
                
                # Check if there is new data, and it isn't our placeholder buffer
                if current_clipboard and current_clipboard != self.last_content:
                    if current_clipboard != CSM_PLACEHOLDER:
                        # Detects plaintext copying -> Execute AES 256 GCM 
                        if self.engine:
                            encrypted_blob = self.engine.encrypt(current_clipboard.encode('utf-8'))
                            
                            # Keep the ciphertext safely locked in memory, NOT on the OS buffer
                            self.internal_cipher = encrypted_blob.hex()
                            
                            # Replace the clipboard buffer natively with a safe placeholder
                            pyperclip.copy(CSM_PLACEHOLDER)
                            self.last_content = CSM_PLACEHOLDER
                    else:
                        self.last_content = current_clipboard
            
            except Exception as e:
                pass
            
            # Polling 200ms per SSS specification
            time.sleep(0.2)

    def _on_paste(self):
        """
        Triggered when a user initiates a PASTE macro (Ctrl+V).
        """
        current_data = pyperclip.paste()
        
        # Ignore empty buffers or native plaintext buffers where our placeholder isn't present
        if current_data != CSM_PLACEHOLDER or not self.internal_cipher:
            return
            
        try:
            raw_blob = bytes.fromhex(self.internal_cipher)
            # Instructs the UI backend to show the Auth dialog cleanly blocking the operation briefly
            if self.paste_callback():
                # Correct Auth
                decrypted_bytes = self.engine.decrypt(raw_blob)
                decrypted_text = decrypted_bytes.decode('utf-8')
                
                # We overwrite the clipboard with the final decrypted text and programmatically PASTE
                self._execute_clean_paste(decrypted_text)
                
        except Exception as e:
            print(f"[ERROR] Decryption Failed - {e}")

    def _execute_clean_paste(self, plaintext: str):
        """
        Uses standard OS bindings to inject the secure plaintext string, and immediately overrides it.
        """
        pyperclip.copy(plaintext)
        self.last_content = plaintext
        
        # To avoid an infinite loop of our own <ctrl>+v hook, we simulate natively by stopping the hook temporarily
        self.listener.stop()
        
        ctrl = keyboard.Controller()
        # Ensure modifying keys are fully depressed before programmatic dispatch
        with ctrl.pressed(keyboard.Key.ctrl):
            ctrl.press('v')
            ctrl.release('v')
        
        # The Application receiving the PASTE event executes almost instantly
        time.sleep(0.15)
        
        # Immediately overwrite the system clipboard buffer per SSS specification back to the placeholder
        pyperclip.copy(CSM_PLACEHOLDER)
        self.last_content = CSM_PLACEHOLDER
        
        # Reinstate hook mechanism safely
        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+v': self._on_paste
        })
        self.listener.start()
