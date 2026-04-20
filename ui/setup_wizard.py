import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
import re
from core import auth
from core.config import resource_path

class SetupWizard(ctk.CTk):
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

        self.title("CSM Initialization Sequence")
        self.geometry("900x600")
        self.resizable(False, False)
        
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        # =========================
        # BACKGROUND IMAGE
        # =========================
        try:
            bg_path = resource_path("ui/background1.png")
            self.bg_image = ctk.CTkImage(
                light_image=Image.open(bg_path),
                dark_image=Image.open(bg_path),
                size=(900, 600)
            )
            self.bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
            self.bg_label.place(relwidth=1, relheight=1)
            self.bg_label.lower()
        except Exception:
            self.configure(fg_color=self.DARK_BG)
        
        # Enable solid background for light mode to override tech imagery if needed
        if ctk.get_appearance_mode() == "Light":
            self.configure(fg_color=self.DARK_BG)
            try: self.bg_label.destroy()
            except: pass

        # Container for pages to allow stacking
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

        self._setup_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self._setup_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

        self._otp_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self._otp_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

        self._build_setup_screen()
        self._build_otp_screen()
        self._setup_frame.tkraise()

    # ─── Screen 1: Email + Password ──────────────────────────────────────
    def _build_setup_screen(self):
        f = self._setup_frame

        # TITLE
        glow = ctk.CTkLabel(f, text="MASTER ACCOUNT INITIALIZATION",
                            font=("Arial", 28, "bold"), text_color=self.BORDER_RED)
        glow.place(relx=0.502, rely=0.152, anchor="center")

        title = ctk.CTkLabel(f, text="MASTER ACCOUNT INITIALIZATION",
                             font=("Orbitron", 28, "bold"), text_color=self.NEON_RED)
        title.place(relx=0.5, rely=0.15, anchor="center")

        desc = ctk.CTkLabel(f, text="Secure your workstation by creating a unified master vault.\nAn OTP will be dispatched to verify your identity.",
                             font=("Consolas", 14), text_color=self.TEXT_GRAY, justify="center")
        desc.place(relx=0.5, rely=0.25, anchor="center")

        # --- EMAIL FIELD ---
        email_wrap = ctk.CTkFrame(f, width=500, height=45, corner_radius=15,
                                  border_width=2, border_color=self.BORDER_RED, fg_color=self.ENTRY_BG)
        email_wrap.place(relx=0.5, rely=0.38, anchor="center")
        email_wrap.pack_propagate(False)

        try:
            mail_img = ctk.CTkImage(light_image=Image.open(resource_path("ui/mail.png")),
                                    dark_image=Image.open(resource_path("ui/mail.png")), size=(20, 20))
            mail_icon = ctk.CTkLabel(email_wrap, image=mail_img, text="")
            mail_icon.pack(side="left", padx=(15, 10))
        except: pass

        self.email_entry = ctk.CTkEntry(email_wrap, placeholder_text="Recovery Email address...",
                                        border_width=0, fg_color="transparent",
                                        text_color=("#1A1A1A", "#FFFFFF"), font=("Consolas", 14))
        self.email_entry.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # --- PASSWORD FIELD ---
        pw_wrap = ctk.CTkFrame(f, width=500, height=45, corner_radius=15,
                               border_width=2, border_color=self.BORDER_RED, fg_color=self.ENTRY_BG)
        pw_wrap.place(relx=0.5, rely=0.48, anchor="center")
        pw_wrap.pack_propagate(False)

        try:
            lock_img = ctk.CTkImage(light_image=Image.open(resource_path("ui/padlock1.png")),
                                    dark_image=Image.open(resource_path("ui/padlock1.png")), size=(20, 20))
            lock_icon = ctk.CTkLabel(pw_wrap, image=lock_img, text="")
            lock_icon.pack(side="left", padx=(15, 10))
        except: pass

        self.password_entry = ctk.CTkEntry(pw_wrap, placeholder_text="New Master Password...",
                                           show="*", border_width=0, fg_color="transparent",
                                           text_color=("#1A1A1A", "#FFFFFF"), font=("Consolas", 14))
        self.password_entry.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # --- CONFIRM FIELD ---
        confirm_wrap = ctk.CTkFrame(f, width=500, height=45, corner_radius=15,
                                    border_width=2, border_color=self.BORDER_RED, fg_color=self.ENTRY_BG)
        confirm_wrap.place(relx=0.5, rely=0.58, anchor="center")
        confirm_wrap.pack_propagate(False)

        try:
            lock2_img = ctk.CTkImage(light_image=Image.open(resource_path("ui/padlock2.png")),
                                     dark_image=Image.open(resource_path("ui/padlock2.png")), size=(20, 20))
            lock2_icon = ctk.CTkLabel(confirm_wrap, image=lock2_img, text="")
            lock2_icon.pack(side="left", padx=(15, 10))
        except: pass

        self.confirm_entry = ctk.CTkEntry(confirm_wrap, placeholder_text="Confirm Master Password...",
                                          show="*", border_width=0, fg_color="transparent",
                                          text_color=("#1A1A1A", "#FFFFFF"), font=("Consolas", 14))
        self.confirm_entry.pack(side="left", fill="both", expand=True, padx=(0, 15))


        self.requirement = ctk.CTkLabel(f,
                                   text="Requires: 8+ chars, Uppercase, Lowercase, Number, Symbol",
                                   font=("Consolas", 12), text_color=self.TEXT_GRAY)
        self.requirement.place(relx=0.5, rely=0.65, anchor="center")

        # SUBMIT BUTTON
        self.init_button = ctk.CTkButton(
            f, text="INITIALIZE PROTOCOL", width=420, height=60, corner_radius=30,
            fg_color=self.HOVER_RED, border_width=2, border_color=self.NEON_RED,
            hover_color=self.PANEL_BG, text_color=self.NEON_RED,
            font=("Orbitron", 18, "bold"), command=self._submit_setup
        )
        self.init_button.place(relx=0.5, rely=0.78, anchor="center")

    def _submit_setup(self):
        email = self.email_entry.get().strip()
        pw1   = self.password_entry.get()
        pw2   = self.confirm_entry.get()

        if not email or not pw1 or not pw2:
            messagebox.showerror("Error", "All fields are required!")
            return
        if not auth.validate_email_format(email):
            messagebox.showerror("Error", "Enter a valid email address!")
            return
        if not auth.validate_password_complexity(pw1):
            messagebox.showerror("Weak Password", "Requires 8+ chars, Uppercase, Lowercase, Number, Symbol.")
            return
        if pw1 != pw2:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        self.init_button.configure(text="DISPATCHING OTP...", state="disabled")
        self.update()

        if auth.generate_and_send_recovery_otp(target_email=email):
            self._otp_hint.configure(text=f"A 6-digit code was sent to  {email}")
            self._otp_frame.tkraise()
        else:
            messagebox.showerror("Error", "Failed to send email. Check connection.")
            self.init_button.configure(text="INITIALIZE PROTOCOL", state="normal")

    # ─── Screen 2: OTP ───────────────────────────────────────────────────
    def _build_otp_screen(self):
        f = self._otp_frame

        glow = ctk.CTkLabel(f, text="VERIFY YOUR IDENTITY",
                            font=("Arial", 28, "bold"), text_color=self.BORDER_RED)
        glow.place(relx=0.502, rely=0.202, anchor="center")

        title = ctk.CTkLabel(f, text="VERIFY YOUR IDENTITY",
                             font=("Orbitron", 28, "bold"), text_color=self.NEON_RED)
        title.place(relx=0.5, rely=0.2, anchor="center")

        self._otp_hint = ctk.CTkLabel(f, text="A 6-digit code was sent to your email.",
                                     font=("Consolas", 14), text_color=self.TEXT_GRAY)
        self._otp_hint.place(relx=0.5, rely=0.32, anchor="center")

        self._otp_entry = ctk.CTkEntry(f, placeholder_text="Enter 6-Digit Code...",
                                     width=300, height=50, corner_radius=15,
                                     border_width=2, border_color=self.BORDER_RED,
                                     fg_color=self.ENTRY_BG, text_color=("#000000", "#FFFFFF"),
                                     justify="center", font=("Consolas", 20, "bold"))
        self._otp_entry.place(relx=0.5, rely=0.45, anchor="center")

        self.verify_button = ctk.CTkButton(
            f, text="VERIFY & COMPLETE SETUP", width=420, height=60, corner_radius=30,
            fg_color=self.HOVER_RED, border_width=2, border_color=self.NEON_RED,
            hover_color=self.PANEL_BG, text_color=self.NEON_RED,
            font=("Orbitron", 18, "bold"), command=self._submit_otp
        )
        self.verify_button.place(relx=0.5, rely=0.6, anchor="center")

        ctk.CTkButton(
            f, text="< Back", width=120, height=35, corner_radius=10,
            fg_color="transparent", border_width=1, border_color=self.BORDER_RED,
            text_color=self.NEON_RED, command=lambda: self._setup_frame.tkraise()
        ).place(relx=0.5, rely=0.72, anchor="center")

    def _submit_otp(self):
        otp = self._otp_entry.get().strip()
        pw  = self.password_entry.get()
        email = self.email_entry.get().strip()

        if auth.reset_password_with_otp(otp, pw):
            auth.save_user_email(email)
            messagebox.showinfo("Success", "System Initialized Successfully 🔐")
            self.destroy()
        else:
            messagebox.showerror("Error", "Invalid or expired OTP code.")

def run_wizard():
    """Launch the setup wizard."""
    ctk.set_appearance_mode("dark")
    app = SetupWizard()
    app.mainloop()
