import customtkinter as ctk
from core import database, auth
from core.config import resource_path

class DashboardUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Clipboard Security Manager - Sentinel Dashboard")
        self.geometry("600x450")
        
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass
        
        # Ensure a clean grid config supporting navigation and main sections
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Main Navigation Side Bar layout setup
        self.sidebar_frame = ctk.CTkFrame(self, width=150, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(3, weight=1)
        
        self.sidebar_title = ctk.CTkLabel(self.sidebar_frame, text="CSM SYSTEM", font=("Consolas", 18, "bold"), text_color="#00FFFF")
        self.sidebar_title.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.btn_logs = ctk.CTkButton(self.sidebar_frame, text="Log History", command=self._show_logs, fg_color="transparent", border_width=1, border_color="#00FFFF")
        self.btn_logs.grid(row=1, column=0, padx=20, pady=10)

        self.btn_auth = ctk.CTkButton(self.sidebar_frame, text="Security Config", command=self._show_recovery, fg_color="transparent", border_width=1, border_color="#00FFFF")
        self.btn_auth.grid(row=2, column=0, padx=20, pady=10)

        # Dynamic Main Center Frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # We start on standard Log view
        self._show_logs()

    def _show_logs(self):
        """Builds a scrolling list of intercepted events."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        lbl = ctk.CTkLabel(self.main_frame, text="RECENT ACTIVITY LOGS", font=("Consolas", 18, "bold"), text_color="#00FFFF")
        lbl.pack(pady=10)

        scrollable_frame = ctk.CTkScrollableFrame(self.main_frame)
        scrollable_frame.pack(fill="both", expand=True)
        
        logs = database.get_recent_logs()
        
        if not logs:
            ctk.CTkLabel(scrollable_frame, text="[ System Logs Empty ]", font=("Consolas", 12)).pack(pady=10)
        
        for idx, event in enumerate(logs):
            txt = f"[{event['timestamp'][:19]}]  {event['event_type']}"
            entry = ctk.CTkLabel(scrollable_frame, text=txt, font=("Consolas", 12), text_color="#DDDDDD" if "FAILED" not in event['event_type'] else "#FF5555")
            entry.pack(anchor="w", padx=10, pady=5)

    def _show_recovery(self):
        """Displays Password Management and remote OTP generation tools."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        lbl = ctk.CTkLabel(self.main_frame, text="MASTER RECOVERY", font=("Consolas", 18, "bold"), text_color="#00FFFF")
        lbl.pack(pady=10)

        info = ctk.CTkLabel(self.main_frame, text="Request a One-Time-Password to be sent to your\nemail before changing the vault password.", font=("Consolas", 12))
        info.pack(pady=10)

        self.btn_req_otp = ctk.CTkButton(self.main_frame, text="DISPATCH OTP EMAIL", fg_color="#005555", command=self._send_otp_flow)
        self.btn_req_otp.pack(pady=10)
        
        self.recovery_msg = ctk.CTkLabel(self.main_frame, text="", text_color="#FFFF00")
        self.recovery_msg.pack(pady=5)
        
        # Fields Hidden Until OTP Sent
        self.otp_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Enter 6-Digit OTP...", width=200, border_color="#00FFFF", fg_color="transparent")
        self.new_pwd_entry = ctk.CTkEntry(self.main_frame, placeholder_text="New Password...", show="*", width=200, border_color="#00FFFF", fg_color="transparent")
        
        self.btn_apply = ctk.CTkButton(self.main_frame, text="APPLY NEW HASH", border_width=1, fg_color="transparent", command=self._apply_new_password)

    def _send_otp_flow(self):
        self.recovery_msg.configure(text="Dispatching OTP...", text_color="#FFFF00")
        self.update_idletasks() # Flush graphics quickly
        
        if auth.generate_and_send_recovery_otp():
            self.recovery_msg.configure(text="Dispatched OTP Successfully! Check Inbox.", text_color="#00FF00")
            # Show the password entry logic dynamically
            self.otp_entry.pack(pady=10)
            self.new_pwd_entry.pack(pady=10)
            self.btn_apply.pack(pady=10)
        else:
            self.recovery_msg.configure(text="Delivery Failed. Check config.py DUMMY data.", text_color="#FF5555")

    def _apply_new_password(self):
        otp = self.otp_entry.get()
        pwd = self.new_pwd_entry.get()
        
        if not auth.validate_password_complexity(pwd):
            self.recovery_msg.configure(text="Requires 8+ Chars, Upper/Lowercase, Num, & Symbol.", text_color="#FF5555")
            return
            
        if auth.reset_password_with_otp(otp, pwd):
            self.recovery_msg.configure(text="Password Override Successful!", text_color="#00FF00")
            self.otp_entry.pack_forget()
            self.new_pwd_entry.pack_forget()
            self.btn_apply.pack_forget()
        else:
            self.recovery_msg.configure(text="INVALID OTP CODE ENCOUNTERED.", text_color="#FF5555")

def launch_dashboard():
    """Builds and loops the dynamic CSM UI window explicitly."""
    app = DashboardUI()
    app.mainloop()
