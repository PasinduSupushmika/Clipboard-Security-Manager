import customtkinter as ctk
from PIL import Image
from core import auth, escalation
from core.config import resource_path

class AuthDialog(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        
        # 🎨 DUAL-THEME COLOR PALETTE
        self.NEON_RED = ("#CC0000", "#FF3333")
        self.BORDER_RED = ("#AAAAAA", "#CC0000")
        self.DARK_BG = ("#F5F5F5", "#050505")
        self.ENTRY_BG = ("#FFFFFF", "#0D0505")
        self.HOVER_RED = ("#FFEEEE", "#5A0000")
        self.TEXT_GRAY = ("#444444", "#AAAAAA")
        self.PANEL_BG = ("#FFFFFF", "#0A0000")
        self.DARK_RED = "#180000"

        self.title("CSM Authorization")
        self.geometry("450x300")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color=self.DARK_BG)
        
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass
        
        self.success = False

        # Futuristic layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.header = ctk.CTkLabel(
            self, text="SECURE CLIPBOARD ACCESS", 
            font=("Consolas", 20, "bold"), text_color=self.NEON_RED
        )
        self.header.grid(row=0, column=0, pady=(30, 5))

        self.info_text = ctk.CTkLabel(
            self, text="Authentication required to decrypt clipboard payload.\nThis action is logged.",
            font=("Consolas", 12), text_color=self.TEXT_GRAY
        )
        self.info_text.grid(row=1, column=0, pady=(0, 20))

        # --- PASSWORD FIELD ---
        pw_wrap = ctk.CTkFrame(self, width=300, height=45, corner_radius=15,
                                border_width=2, border_color=self.BORDER_RED, fg_color=self.ENTRY_BG)
        pw_wrap.grid(row=2, column=0, pady=10)
        pw_wrap.pack_propagate(False)

        try:
            self.lock_img = ctk.CTkImage(light_image=Image.open(resource_path("ui/padlock_glow.png")),
                                         dark_image=Image.open(resource_path("ui/padlock_glow.png")), size=(20, 20))
            self.lock_icon = ctk.CTkLabel(pw_wrap, image=self.lock_img, text="")
            self.lock_icon.pack(side="left", padx=(15, 10))
        except: pass

        self.password_entry = ctk.CTkEntry(
            pw_wrap, placeholder_text="Enter Master Password...",
            show="*", border_width=0, fg_color="transparent",
            font=("Consolas", 14), text_color=("#000000", "#FFFFFF"), placeholder_text_color="#888888"
        )
        self.password_entry.pack(side="left", fill="both", expand=True, padx=(0, 15))
        self.password_entry.bind('<Return>', lambda event: self._verify())

        self.btn_submit = ctk.CTkButton(
            self, text="DECRYPT", width=250, height=45, fg_color=self.HOVER_RED, 
            border_width=2, border_color=self.NEON_RED, hover_color=self.PANEL_BG, 
            text_color=self.NEON_RED, font=("Consolas", 14, "bold"), corner_radius=8,
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
            self.info_text.configure(text="SYSTEM LOCKEDOUT. Check your Email.", text_color=self.NEON_RED)
            return
            
        validated = auth.verify_master_password(pwd)
        result = escalation.record_attempt(validated)

        if result["action"] == "ALLOW":
            self.success = True
            self.destroy()
        elif result["action"] == "DENY":
            self.password_entry.delete(0, 'end')
            self.info_text.configure(text=result["message"], text_color=self.NEON_RED)
        elif result["action"] == "LOCKOUT":
            self.info_text.configure(text=result["message"], text_color=self.NEON_RED)
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
