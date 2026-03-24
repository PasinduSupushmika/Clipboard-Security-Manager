import customtkinter as ctk
from core import auth, escalation
from core.config import resource_path

class AuthDialog(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        
        self.title("CSM Authorization")
        self.geometry("400x250")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass
        
        self.success = False

        # Futuristic layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.header = ctk.CTkLabel(
            self, text="Secure Clipboard Access", 
            font=("Consolas", 20, "bold"), text_color="#00FFFF"
        )
        self.header.grid(row=0, column=0, pady=(20, 10))

        self.info_text = ctk.CTkLabel(
            self, text="Authentication required to decrypt clipboard payload.\nThis action is logged.",
            font=("Consolas", 12)
        )
        self.info_text.grid(row=1, column=0, pady=(0, 20))

        self.password_entry = ctk.CTkEntry(
            self, placeholder_text="Enter Master Password...",
            show="*", width=250, border_color="#00FFFF", fg_color="transparent"
        )
        self.password_entry.grid(row=2, column=0, pady=10)
        self.password_entry.bind('<Return>', lambda event: self._verify())

        self.btn_submit = ctk.CTkButton(
            self, text="DECRYPT", width=150, fg_color="transparent", 
            border_width=2, hover_color="#005555", text_color="#00FFFF",
            command=self._verify
        )
        self.btn_submit.grid(row=3, column=0, pady=20)

        # Focus instantly
        self.password_entry.focus_force()

        # Handle X button safely
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _verify(self):
        pwd = self.password_entry.get()
        
        # Check standard Lockout Protocol First
        if escalation.is_locked():
            self.info_text.configure(text="SYSTEM LOCKEDOUT. Check your Email.", text_color="#FF0000")
            return
            
        validated = auth.verify_master_password(pwd)
        result = escalation.record_attempt(validated)

        if result["action"] == "ALLOW":
            self.success = True
            self.destroy()
        elif result["action"] == "DENY":
            self.password_entry.delete(0, 'end')
            self.info_text.configure(text=result["message"], text_color="#FF5555")
        elif result["action"] == "LOCKOUT":
            self.info_text.configure(text=result["message"], text_color="#FF0000")
            self.password_entry.configure(state="disabled")
            self.btn_submit.configure(state="disabled")

    def _cancel(self):
        self.success = False
        self.destroy()

def request_authorization() -> bool:
    """Spawns an isolated modal instance to request decryption approval natively."""
    
    # We must construct a hidden root if one doesn't exist, as our primary execution is background hooking
    root = ctk.CTk()
    root.withdraw()
    
    dialog = AuthDialog(root)
    # Halt progression asynchronously until the UI finishes evaluation
    root.wait_window(dialog)
    root.destroy()
    
    return dialog.success
