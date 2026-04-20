import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
from core import database, auth, crypto
from core.config import resource_path

class DashboardUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 🎨 DUAL-THEME COLOR PALETTE
        self.NEON_RED = ("#CC0000", "#FF3333")
        self.BORDER_RED = ("#AAAAAA", "#CC0000")
        self.DARK_BG = ("#F5F5F5", "#050505")
        self.ENTRY_BG = ("#FFFFFF", "#0D0505")
        self.HOVER_RED = ("#FFEEEE", "#5A0000")
        self.TEXT_GRAY = ("#444444", "#AAAAAA")
        self.PANEL_BG = ("#FFFFFF", "#0A0000")

        self.title("Clipboard Security Manager - Sentinel Dashboard")
        self.geometry("700x500")
        self.configure(fg_color=self.DARK_BG)
        
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass
        
        # Ensure a clean grid config supporting navigation and main sections
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Main Navigation Side Bar layout setup
        self.sidebar_frame = ctk.CTkFrame(self, width=150, corner_radius=0, fg_color=self.PANEL_BG)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(3, weight=1)
        
        self.sidebar_title = ctk.CTkLabel(self.sidebar_frame, text="CSM SYSTEM", font=("Consolas", 18, "bold"), text_color=self.NEON_RED)
        self.sidebar_title.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.btn_logs = ctk.CTkButton(self.sidebar_frame, text="Log History", command=self._show_logs, fg_color="transparent", border_width=1, border_color=self.BORDER_RED, hover_color=self.HOVER_RED, text_color=self.NEON_RED, font=("Consolas", 13, "bold"))
        self.btn_logs.grid(row=1, column=0, padx=20, pady=10)

        self.btn_auth = ctk.CTkButton(self.sidebar_frame, text="Security Config", command=self._show_recovery, fg_color="transparent", border_width=1, border_color=self.BORDER_RED, hover_color=self.HOVER_RED, text_color=self.NEON_RED, font=("Consolas", 13, "bold"))
        self.btn_auth.grid(row=2, column=0, padx=20, pady=10)

        # Dynamic Main Center Frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # We start on standard Log view
        
        self.btn_theme = ctk.CTkButton(self.sidebar_frame, text="Toggle Theme", command=self._toggle_theme, fg_color="transparent", border_width=1, border_color=self.BORDER_RED, hover_color=self.HOVER_RED, text_color=self.TEXT_GRAY, font=("Consolas", 12))
        self.btn_theme.grid(row=3, column=0, padx=20, pady=20, sticky="s")
        self._show_logs()
        
    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Light" if current == "Dark" else "Dark")

    def _show_logs(self):
        """Builds a scrolling list of intercepted events."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        lbl = ctk.CTkLabel(self.main_frame, text="RECENT ACTIVITY LOGS", font=("Consolas", 20, "bold"), text_color=self.NEON_RED)
        lbl.pack(pady=(10, 20))

        scrollable_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=self.PANEL_BG)
        scrollable_frame.pack(fill="both", expand=True)
        
        logs = database.get_recent_logs()
        
        if not logs:
            ctk.CTkLabel(scrollable_frame, text="[ System Logs Empty ]", font=("Consolas", 12), text_color=self.TEXT_GRAY).pack(pady=20)
        
        for idx, event in enumerate(logs):
            txt = f"[{event['timestamp'][:19]}]  {event['event_type']}"
            
            # Interactive entries for on-demand decryption
            entry = ctk.CTkButton(
                scrollable_frame, text=txt, font=("Consolas", 13),
                anchor="w", fg_color="transparent", 
                text_color=self.TEXT_GRAY if "FAILED" not in event['event_type'] else self.NEON_RED,
                hover_color=self.HOVER_RED,
                command=lambda e=event: self._view_log_detail(e)
            )
            entry.pack(fill="x", padx=10, pady=2)

    def _view_log_detail(self, event: dict):
        """On-demand decryption of event payloads."""
        try:
            # Reconstruct the engine with the resident Master Key
            engine = crypto.CryptoEngine(auth.get_aes_runtime_key())
            payload_bytes = event["encrypted_payload"]
            
            try:
                decrypted_msg = engine.decrypt(payload_bytes).decode("utf-8")
                detail_title = f"Event Detail: {event['event_type']}"
            except Exception:
                # Fallback for Legacy Plaintext logs (older entries)
                try:
                    decrypted_msg = payload_bytes.decode("utf-8")
                    detail_title = f"Legacy Event Detail: {event['event_type']}"
                except:
                    raise Exception("Payload is neither valid GCM ciphertext nor valid Plaintext UTF-8.")

            messagebox.showinfo(
                detail_title,
                f"Timestamp: {event['timestamp']}\n\n"
                f"Payload Content:\n{decrypted_msg}"
            )
        except Exception as e:
            messagebox.showerror("Monitoring Error", f"Failed to resolve log detail: {e}")

    def _show_recovery(self):
        """Displays Password Management and remote OTP generation tools."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        lbl = ctk.CTkLabel(self.main_frame, text="MASTER RECOVERY", font=("Consolas", 20, "bold"), text_color=self.NEON_RED)
        lbl.pack(pady=(10, 10))

        info = ctk.CTkLabel(self.main_frame, text="Request a One-Time-Password to be sent to your\nemail before changing the vault password.", font=("Consolas", 13), text_color=self.TEXT_GRAY)
        info.pack(pady=10)

        self.btn_req_otp = ctk.CTkButton(self.main_frame, text="DISPATCH OTP EMAIL", fg_color=self.HOVER_RED, border_width=2, border_color=self.NEON_RED, hover_color=self.PANEL_BG, text_color=self.NEON_RED, font=("Consolas", 14, "bold"), width=300, height=45, corner_radius=8, command=self._send_otp_flow)
        self.btn_req_otp.pack(pady=20)
        
        self.recovery_msg = ctk.CTkLabel(self.main_frame, text="", text_color=self.TEXT_GRAY, font=("Consolas", 12))
        self.recovery_msg.pack(pady=5)
        
        # Fields Hidden Until OTP Sent
        # --- OTP FIELD ---
        self.otp_wrap = ctk.CTkFrame(self.main_frame, width=300, height=45, corner_radius=15,
                                     border_width=2, border_color=self.BORDER_RED, fg_color=self.ENTRY_BG)
        self.otp_wrap.pack_propagate(False)

        try:
            self.mail_img = ctk.CTkImage(light_image=Image.open(resource_path("ui/mail_glow.png")),
                                         dark_image=Image.open(resource_path("ui/mail_glow.png")), size=(20, 20))
            self.mail_icon = ctk.CTkLabel(self.otp_wrap, image=self.mail_img, text="")
            self.mail_icon.pack(side="left", padx=(15, 10))
        except: pass

        self.otp_entry = ctk.CTkEntry(self.otp_wrap, placeholder_text="Enter 6-Digit OTP...", 
                                      border_width=0, fg_color="transparent", 
                                      text_color=("#000000", "#FFFFFF"), font=("Consolas", 14))
        self.otp_entry.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # --- NEW PASSWORD FIELD ---
        self.pw_wrap = ctk.CTkFrame(self.main_frame, width=300, height=45, corner_radius=15,
                                    border_width=2, border_color=self.BORDER_RED, fg_color=self.ENTRY_BG)
        self.pw_wrap.pack_propagate(False)

        try:
            self.lock_img = ctk.CTkImage(light_image=Image.open(resource_path("ui/padlock_glow.png")),
                                         dark_image=Image.open(resource_path("ui/padlock_glow.png")), size=(20, 20))
            self.lock_icon = ctk.CTkLabel(self.pw_wrap, image=self.lock_img, text="")
            self.lock_icon.pack(side="left", padx=(15, 10))
        except: pass

        self.new_pwd_entry = ctk.CTkEntry(self.pw_wrap, placeholder_text="New Password...", 
                                          show="*", border_width=0, fg_color="transparent", 
                                          text_color=("#000000", "#FFFFFF"), font=("Consolas", 14))
        self.new_pwd_entry.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        self.btn_apply = ctk.CTkButton(self.main_frame, text="APPLY NEW HASH", width=300, height=45, fg_color=self.HOVER_RED, border_width=2, border_color=self.NEON_RED, hover_color=self.PANEL_BG, text_color=self.NEON_RED, font=("Consolas", 14, "bold"), corner_radius=8, command=self._apply_new_password)

    def _send_otp_flow(self):
        self.recovery_msg.configure(text="Dispatching OTP...", text_color=self.TEXT_GRAY)
        self.update_idletasks() # Flush graphics quickly
        
        if auth.generate_and_send_recovery_otp():
            self.recovery_msg.configure(text="Dispatched OTP Successfully! Check Inbox.", text_color=self.NEON_RED)
            # Show the password entry logic dynamically
            self.otp_wrap.pack(pady=10)
            self.pw_wrap.pack(pady=10)
            self.btn_apply.pack(pady=20)
        else:
            self.recovery_msg.configure(text="Delivery Failed. Check config.py DUMMY data.", text_color=self.NEON_RED)

    def _apply_new_password(self):
        otp = self.otp_entry.get()
        pwd = self.new_pwd_entry.get()
        
        if not auth.validate_password_complexity(pwd):
            self.recovery_msg.configure(text="Requires 8+ Chars, Upper/Lowercase, Num, & Symbol.", text_color=self.NEON_RED)
            return
            
        if auth.reset_password_with_otp(otp, pwd):
            self.recovery_msg.configure(text="Password Override Successful!", text_color=self.NEON_RED)
            self.otp_wrap.pack_forget()
            self.pw_wrap.pack_forget()
            self.btn_apply.pack_forget()
        else:
            self.recovery_msg.configure(text="INVALID OTP CODE ENCOUNTERED.", text_color=self.NEON_RED)

def launch_dashboard():
    """Builds and loops the dynamic CSM UI window explicitly."""
    app = DashboardUI()
    app.mainloop()
