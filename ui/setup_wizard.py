import customtkinter as ctk
from core import auth
from core.config import resource_path

class SetupWizard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CSM Initialization Sequence")
        self.geometry("480x520")
        self.resizable(False, False)
        
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass

        # Apply Modern Dark Glow UI Pattern Native Frame Config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        self.setup_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.setup_frame.grid(row=0, column=0, sticky="nsew")
        self.setup_frame.grid_columnconfigure(0, weight=1)
        
        self.otp_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.otp_frame.grid(row=0, column=0, sticky="nsew")
        self.otp_frame.grid_columnconfigure(0, weight=1)

        self._build_setup_frame()
        self._build_otp_frame()
        
        self.setup_frame.tkraise()

    def _build_setup_frame(self):
        # Cyberpunkish Labeling Scheme
        header = ctk.CTkLabel(
            self.setup_frame, text="MASTER PASSWORD SETUP",
            font=("Consolas", 22, "bold"), text_color="#00FFFF"
        )
        header.grid(row=0, column=0, pady=(30, 5))

        info = ctk.CTkLabel(
            self.setup_frame, text="Choose a strong password to encrypt clipboard buffers.\nYou must provide a valid Email for recovery OTPs.",
            font=("Consolas", 12), text_color="#AAAAAA"
        )
        info.grid(row=1, column=0, pady=(0, 20))

        # Email Capture
        self.email_entry = ctk.CTkEntry(
            self.setup_frame, placeholder_text="Recovery Email (@gmail.com)...",
            width=300, border_color="#00FFFF", fg_color="transparent"
        )
        self.email_entry.grid(row=2, column=0, pady=(10, 20))

        # Setup PW Data
        self.pw_entry = ctk.CTkEntry(
            self.setup_frame, placeholder_text="New Master Password...",
            show="*", width=300, border_color="#00FFFF", fg_color="transparent"
        )
        self.pw_entry.grid(row=3, column=0, pady=5)

        self.pw_confirm = ctk.CTkEntry(
            self.setup_frame, placeholder_text="Confirm Master Password...",
            show="*", width=300, border_color="#00FFFF", fg_color="transparent"
        )
        self.pw_confirm.grid(row=4, column=0, pady=5)
        
        pw_rules = ctk.CTkLabel(self.setup_frame, text="Requires: 8+ chars, Uppercase, Lowercase, Number, Symbol.", text_color="#777777", font=("Consolas", 10))
        pw_rules.grid(row=5, column=0, pady=(0, 10))

        self.error_lbl = ctk.CTkLabel(self.setup_frame, text="", text_color="#FF5555", font=("Consolas", 12))
        self.error_lbl.grid(row=6, column=0, pady=(5, 0))

        self.btn_submit = ctk.CTkButton(
            self.setup_frame, text="INITIALIZE PROTOCOL", width=200, fg_color="transparent", 
            border_width=2, hover_color="#005555", text_color="#00FFFF",
            command=self._attempt_initialization
        )
        self.btn_submit.grid(row=7, column=0, pady=20)

    def _build_otp_frame(self):
        header = ctk.CTkLabel(
            self.otp_frame, text="VERIFY EMAIL ADDRESS",
            font=("Consolas", 22, "bold"), text_color="#00FFFF"
        )
        header.grid(row=0, column=0, pady=(60, 10))

        info = ctk.CTkLabel(
            self.otp_frame, text="A test OTP has been dispatched to your email.\nPlease enter it below to confirm you can receive alerts.",
            font=("Consolas", 12), text_color="#AAAAAA"
        )
        info.grid(row=1, column=0, pady=(0, 30))

        self.otp_entry = ctk.CTkEntry(
            self.otp_frame, placeholder_text="Enter 6-Digit Code...",
            width=200, border_color="#00FFFF", fg_color="transparent", justify="center"
        )
        self.otp_entry.grid(row=2, column=0, pady=10)

        self.otp_error_lbl = ctk.CTkLabel(self.otp_frame, text="", text_color="#FFFF00", font=("Consolas", 12))
        self.otp_error_lbl.grid(row=3, column=0, pady=(5, 0))

        self.btn_verify = ctk.CTkButton(
            self.otp_frame, text="VERIFY & COMPLETE SETUP", width=200, fg_color="transparent", 
            border_width=2, hover_color="#005555", text_color="#00FFFF",
            command=self._verify_otp_completion
        )
        self.btn_verify.grid(row=4, column=0, pady=30)
        
        btn_back = ctk.CTkButton(self.otp_frame, text="< Back", width=100, fg_color="transparent", border_width=1, command=lambda: self.setup_frame.tkraise())
        btn_back.grid(row=5, column=0)

    def _attempt_initialization(self):
        e = self.email_entry.get()
        p1 = self.pw_entry.get()
        p2 = self.pw_confirm.get()
        
        if not auth.validate_email_format(e):
            self.error_lbl.configure(text="Email must be a valid @gmail.com address.")
            return

        if not auth.validate_password_complexity(p1):
            self.error_lbl.configure(text="Password fails complexity requirements.")
            return
            
        if p1 != p2:
            self.error_lbl.configure(text="Passwords do not match!")
            return
            
        self.error_lbl.configure(text="Dispatching Test Email...", text_color="#FFFF00")
        self.update()
        
        if auth.generate_and_send_recovery_otp(target_email=e):
            self.error_lbl.configure(text="", text_color="#FF5555")
            self.otp_error_lbl.configure(text="Sent!", text_color="#00FF00")
            self.otp_frame.tkraise()
        else:
            self.error_lbl.configure(text="Failed to send Verification Email. Check connection or Dummy data.")
            self.update()

    def _verify_otp_completion(self):
        otp = self.otp_entry.get()
        # We temporarily hijack the reset_password_with_otp logic by parsing the temporary password securely
        p1 = self.pw_entry.get()
        
        if auth.reset_password_with_otp(otp, p1):
            # Save the email permanently since they validated it works
            auth.save_user_email(self.email_entry.get())
            self.destroy() # Close the UI, setup complete!
        else:
            self.otp_error_lbl.configure(text="Invalid OTP Code.", text_color="#FF5555")

def run_wizard():
    """Boots the wizard synchronously. Usually invoked by main.py if unconfigured."""
    app = SetupWizard()
    app.mainloop()
