# =============================================================================
# ui/installer_wizard.py  –  Windows Installation & Uninstallation Wizard
# =============================================================================
# 7-page dark-themed installer matching the specified flow:
#
#   1. WelcomePage          – Welcome + existing-install detection
#   2. InformationPage      – Licence / information text
#   3. DestinationPage      – Browse install location
#   4. ComponentsPage       – Desktop shortcut, Start Menu, autostart
#   5. StartMenuPage        – Start Menu folder name
#   6. AdditionalTasksPage  – Extra options (currently: autostart on boot)
#   7. ReadyPage            – Summary before install
#   → ProgressPage          – Progress bar (not a wizard step, auto-shown)
# =============================================================================

import sys
import os
import shutil
import subprocess
import time
import winreg
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from core.config import resource_path

_INSTALL_DIR_NAME = "iMazK_CSM"
_APP_EXE_NAME     = "ClipboardSecurityManager.exe"
_APP_TITLE        = "Clipboard Security Manager"


# =============================================================================
# Main controller window
# =============================================================================
class ProfessionalInstaller(ctk.CTk):

    def __init__(self, current_exe_path: str):
        super().__init__()
        self.current_exe = current_exe_path
        self.install_dir = Path(os.environ.get("LOCALAPPDATA", "")) / _INSTALL_DIR_NAME

        # 🎨 DUAL-THEME COLOR PALETTE
        self.NEON_RED = ("#CC0000", "#FF3333")
        self.BORDER_RED = ("#AAAAAA", "#CC0000")
        self.DARK_BG = ("#F5F5F5", "#050505")
        self.ENTRY_BG = ("#FFFFFF", "#0D0505")
        self.HOVER_RED = ("#FFEEEE", "#5A0000")
        self.TEXT_GRAY = ("#444444", "#AAAAAA")
        self.TEXT_SUB = ("#444444", "#AAAAAA")
        self.PANEL_BG = ("#FFFFFF", "#0A0000")

        self.title(f"iMazK pvt ltd – {_APP_TITLE} Setup")
        self.geometry("640x480")
        self.resizable(False, False)

        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        # Full-window container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # Build all pages
        self.frames = {}
        for PageClass in (
            WelcomePage, InformationPage, DestinationPage,
            ComponentsPage, StartMenuPage, AdditionalTasksPage,
            ReadyPage, ProgressPage
        ):
            name  = PageClass.__name__
            frame = PageClass(parent=self.container, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("WelcomePage")

    def show_frame(self, name: str):
        self.frames[name].tkraise()

    # ── Installation ─────────────────────────────────────────────────────────
    def execute_installation(self):
        prog = self.frames["ProgressPage"]
        dest = self.frames["DestinationPage"]
        comp = self.frames["ComponentsPage"]
        sm   = self.frames["StartMenuPage"]
        add  = self.frames["AdditionalTasksPage"]

        self.install_dir = Path(dest.get_path())
        self.show_frame("ProgressPage")
        self.update()

        # 1 – Overwrite check & Process Termination
        prog.set_status("Closing running application...", 0.1)
        self.update()
        
        # Safe termination of any existing instances
        try:
            subprocess.run(["taskkill", "/F", "/IM", _APP_EXE_NAME, "/T"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1) # Wait for OS to release file locks
        except: pass

        prog.set_status("Extracting files...", 0.2)
        self.update()
        self.install_dir.mkdir(parents=True, exist_ok=True)
        target_exe = self.install_dir / _APP_EXE_NAME
        
        try:
            shutil.copy2(self.current_exe, target_exe)
            # Create hidden installation marker
            (self.install_dir / ".installed").write_text(time.ctime(), encoding="utf-8")
        except Exception as e:
            # If still locked, alert user
            from tkinter import messagebox
            messagebox.showerror("Installation Error", 
                f"Failed to overwrite {target_exe}.\n\nPlease ensure CSM is closed and try again.\n\nError: {e}")
            self.show_frame("WelcomePage") # Go back to start
            return

        # 2 – PowerShell shortcuts
        prog.set_status("Creating shortcuts...", 0.45)
        self.update()
        ps_lines = [
            f'$exe = "{target_exe}"',
            '$ws  = New-Object -ComObject WScript.Shell',
        ]

        if comp.var_desktop.get():
            d = Path(os.environ.get("USERPROFILE", "")) / "Desktop" / f"{_APP_TITLE}.lnk"
            ps_lines += [
                f'$s = $ws.CreateShortcut("{d}")',
                '$s.TargetPath = $exe',
                f'$s.IconLocation = "$exe,0"',
                f'$s.WorkingDirectory = "{self.install_dir}"',
                '$s.Save()',
            ]

        sm_folder = sm.get_folder_name() or _APP_TITLE
        if comp.var_startmenu.get():
            sm_dir = (
                Path(os.environ.get("APPDATA", ""))
                / "Microsoft" / "Windows" / "Start Menu" / "Programs" / sm_folder
            )
            sm_dir.mkdir(parents=True, exist_ok=True)
            for lnk_name, args in [
                (f"{_APP_TITLE}.lnk",   ""),
                ("Uninstall CSM.lnk",   "--uninstall"),
            ]:
                lnk_path = sm_dir / lnk_name
                ps_lines += [
                    f'$s = $ws.CreateShortcut("{lnk_path}")',
                    '$s.TargetPath = $exe',
                    f'$s.Arguments = "{args}"',
                    f'$s.IconLocation = "$exe,0"',
                    f'$s.WorkingDirectory = "{self.install_dir}"',
                    '$s.Save()',
                ]

        ps_file = self.install_dir / "_setup.ps1"
        ps_file.write_text("\n".join(ps_lines), encoding="utf-8")
        subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_file)],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        # 3 – Registry autostart
        prog.set_status("Configuring startup...", 0.75)
        self.update()
        if add.var_boot.get():
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(key, "ClipboardSecurityManager", 0,
                                  winreg.REG_SZ, str(target_exe))
                winreg.CloseKey(key)
            except Exception:
                pass

        # 4 – Launch installed EXE and exit setup
        prog.set_status("Installation complete! Launching application...", 1.0)
        self.update()
        time.sleep(0.8)
        subprocess.Popen([str(target_exe)])
        sys.exit(0)

    # ── Uninstallation ───────────────────────────────────────────────────────
    def execute_uninstall(self):
        prog = self.frames["ProgressPage"]
        prog.header_lbl.configure(text="Uninstalling CSM...")
        self.show_frame("ProgressPage")
        self.update()

        prog.set_status("Removing registry entries...", 0.2)
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, "ClipboardSecurityManager")
            winreg.CloseKey(key)
        except Exception:
            pass

        prog.set_status("Removing shortcuts...", 0.45)
        for lnk in [
            Path(os.environ.get("USERPROFILE", "")) / "Desktop" / f"{_APP_TITLE}.lnk",
            Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu"
            / "Programs" / _APP_TITLE / f"{_APP_TITLE}.lnk",
        ]:
            try:
                lnk.unlink(missing_ok=True)
            except Exception:
                pass

        prog.set_status("Wiping credentials & data...", 0.7)
        try:
            from core import auth
            auth.delete_all_credentials()
        except Exception:
            pass
        try:
            (self.install_dir / ".installed").unlink(missing_ok=True)
            shutil.rmtree(CSM_DATA_DIR, ignore_errors=True)
            shutil.rmtree(str(self.install_dir), ignore_errors=True)
        except Exception:
            pass

        prog.set_status("Uninstallation complete.", 1.0)
        prog.btn_finish.configure(
            state="normal", text="Close", command=lambda: sys.exit(0)
        )
        self.update()


# =============================================================================
# Helper: banner header used by every page
# =============================================================================
def _banner(parent, step: str, title: str):
    """Dual-themed top banner with step label and title."""
    neon_red = ("#CC0000", "#FF3333")
    panel_bg = ("#FFFFFF", "#0A0000")
    text_gray = ("#444444", "#888888")
    
    bar = ctk.CTkFrame(parent, fg_color=panel_bg, corner_radius=0)
    bar.grid(row=0, column=0, sticky="ew", columnspan=10)
    bar.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(bar, text=step,
                 font=("Consolas", 10), text_color=text_gray).grid(row=0, column=0, sticky="w", padx=18, pady=(10,0))
    ctk.CTkLabel(bar, text=title,
                 font=("Consolas", 16, "bold"), text_color=neon_red).grid(row=1, column=0, sticky="w", padx=18, pady=(0,12))


def _nav(parent, controller, back_page: str, next_fn=None, next_label="Next >"):
    """Bottom nav bar with Back / Next buttons and a thin separator."""
    border_red = ("#AAAAAA", "#CC0000")
    neon_red = ("#CC0000", "#FF3333")
    text_main = ("#1A1A1A", "#CCCCCC")
    hover_red = ("#FFEEEE", "#5A0000")
    
    sep = ctk.CTkFrame(parent, height=1, fg_color=border_red)
    sep.grid(row=98, column=0, sticky="ew", padx=0, pady=(10, 0))

    nav = ctk.CTkFrame(parent, fg_color="transparent")
    nav.grid(row=99, column=0, sticky="ew", padx=20, pady=10)
    nav.grid_columnconfigure(0, weight=1)

    ctk.CTkButton(
        nav, text="< Back", width=100,
        fg_color="transparent", border_width=1,
        border_color=border_red, text_color=text_main,
        command=lambda: controller.show_frame(back_page)
    ).grid(row=0, column=0, sticky="w")

    ctk.CTkButton(
        nav, text=next_label, width=120,
        fg_color=hover_red, border_width=2, border_color=neon_red, 
        hover_color=hover_red, text_color=neon_red, font=("Consolas", 13, "bold"),
        command=next_fn
    ).grid(row=0, column=1, sticky="e")


# =============================================================================
# PAGE 1 – Welcome
# =============================================================================
class WelcomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        _banner(self, "Step 1 of 7", f"Welcome to {_APP_TITLE}")

        ctk.CTkLabel(
            self,
            text=f"Welcome to the {_APP_TITLE} Setup Wizard.\n\n"
                 "This wizard will guide you through installing CSM on your computer.\n\n"
                 "It is recommended that you close all other applications\n"
                 "before continuing with the installation.",
            font=("Consolas", 13), text_color=controller.TEXT_SUB, justify="left"
        ).grid(row=1, column=0, padx=30, pady=30, sticky="w")

        sep = ctk.CTkFrame(self, height=1, fg_color=controller.BORDER_RED)
        sep.grid(row=98, column=0, sticky="ew", padx=0, pady=(10, 0))

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=99, column=0, sticky="ew", padx=20, pady=10)
        nav.grid_columnconfigure(0, weight=1)

        # Show uninstall button if already installed
        if controller.install_dir.exists():
            ctk.CTkButton(
                nav, text="Uninstall Existing", width=140,
                fg_color=controller.HOVER_RED, border_width=2, border_color=controller.NEON_RED,
                hover_color=controller.PANEL_BG, text_color=controller.NEON_RED, font=("Consolas", 12, "bold"),
                command=controller.execute_uninstall
            ).grid(row=0, column=0, sticky="w")
        else:
            ctk.CTkLabel(nav, text="").grid(row=0, column=0)

        neon_red = ("#CC0000", "#FF3333")
        hover_red = ("#FFEEEE", "#5A0000")

        ctk.CTkButton(
            nav, text="Next >", width=120,
            fg_color=hover_red, border_width=2, border_color=neon_red, 
            hover_color=hover_red, text_color=neon_red, font=("Consolas", 13, "bold"),
            command=lambda: controller.show_frame("InformationPage")
        ).grid(row=0, column=1, sticky="e")


# =============================================================================
# PAGE 2 – Information
# =============================================================================
class InformationPage(ctk.CTkFrame):
    _INFO = (
        "CLIPBOARD SECURITY MANAGER – END USER INFORMATION\n"
        "═══════════════════════════════════════════════════\n\n"
        "Clipboard Security Manager (CSM) is an enterprise-grade clipboard\n"
        "protection utility developed by iMazK pvt ltd.\n\n"
        "WHAT CSM DOES:\n"
        "  • Intercepts all clipboard copy operations (Ctrl+C)\n"
        "  • Encrypts clipboard data in memory using AES-256-GCM\n"
        "  • Requires master password authentication before each paste (Ctrl+V)\n"
        "  • Sends security alert emails after repeated failed paste attempts\n"
        "  • Logs security events for 30 days in an encrypted local database\n\n"
        "DATA PRIVACY:\n"
        "  • Clipboard content is NEVER written to disk in plaintext\n"
        "  • Master password is stored as an Argon2 hash in the OS Keyring\n"
        "  • Your email address is stored in the OS Keyring for alert delivery\n\n"
        "REQUIREMENTS:\n"
        "  • Windows 10 / 11 (64-bit)\n"
        "  • Active internet connection for email alerts and OTP delivery\n\n"
        "Please read this information carefully before proceeding."
    )

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        _banner(self, "Step 2 of 7", "Information")

        box = ctk.CTkTextbox(
            self, font=("Consolas", 11), text_color=controller.TEXT_SUB,
            fg_color=controller.ENTRY_BG, border_color=controller.BORDER_RED,
            border_width=1, wrap="word"
        )
        box.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        box.insert("end", self._INFO)
        box.configure(state="disabled")

        _nav(self, controller, "WelcomePage",
             next_fn=lambda: controller.show_frame("DestinationPage"))


# =============================================================================
# PAGE 3 – Select Destination Location
# =============================================================================
class DestinationPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._controller = controller

        _banner(self, "Step 3 of 7", "Select Destination Location")

        ctk.CTkLabel(
            self,
            text="Setup will install CSM into the following folder.\n"
                 "To install into a different folder click Browse and select another.",
            font=("Consolas", 12), text_color=controller.TEXT_SUB, justify="left"
        ).grid(row=1, column=0, padx=30, pady=(18, 10), sticky="w")

        path_row = ctk.CTkFrame(self, fg_color="transparent")
        path_row.grid(row=2, column=0, padx=30, sticky="ew")
        path_row.grid_columnconfigure(0, weight=1)

        self._path_var = ctk.StringVar(value=str(controller.install_dir))
        self._path_entry = ctk.CTkEntry(
            path_row, textvariable=self._path_var,
            font=("Consolas", 11), fg_color=controller.ENTRY_BG,
            border_color=controller.BORDER_RED
        )
        self._path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            path_row, text="Browse...", width=90,
            fg_color=controller.HOVER_RED, border_width=1, border_color=controller.NEON_RED,
            hover_color=controller.PANEL_BG, text_color=controller.NEON_RED, font=("Consolas", 11, "bold"),
            command=self._browse
        ).grid(row=0, column=1)

        disk_info = ctk.CTkLabel(
            self, text="At least 80 MB of free disk space is required.",
            font=("Consolas", 10), text_color=controller.TEXT_GRAY
        )
        disk_info.grid(row=3, column=0, padx=30, pady=(10, 0), sticky="w")

        _nav(self, controller, "InformationPage",
             next_fn=lambda: controller.show_frame("ComponentsPage"))

    def _browse(self):
        chosen = filedialog.askdirectory(initialdir=self._path_var.get())
        if chosen:
            self._path_var.set(chosen)
            self._controller.install_dir = Path(chosen)

    def get_path(self) -> str:
        return self._path_var.get()


# =============================================================================
# PAGE 4 – Select Components
# =============================================================================
class ComponentsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        _banner(self, "Step 4 of 7", "Select Components")

        ctk.CTkLabel(
            self,
            text="Select the components you want to install. Clear the checkboxes\n"
                 "for any components you do not wish to install.",
            font=("Consolas", 12), text_color=controller.TEXT_SUB, justify="left"
        ).grid(row=1, column=0, padx=30, pady=(18, 14), sticky="w")

        chk_frame = ctk.CTkFrame(self, fg_color=controller.ENTRY_BG,
                                  corner_radius=6, border_width=1,
                                  border_color=controller.BORDER_RED)
        chk_frame.grid(row=2, column=0, padx=30, sticky="ew")
        chk_frame.grid_columnconfigure(0, weight=1)

        self.var_desktop  = ctk.BooleanVar(value=True)
        self.var_startmenu = ctk.BooleanVar(value=True)

        for row, (var, label, desc) in enumerate([
            (self.var_desktop,   "Desktop Shortcut",
             "Creates a shortcut on the Windows Desktop"),
            (self.var_startmenu, "Start Menu Entry",
             "Creates entries in the Start Menu (includes Uninstaller)"),
        ]):
            r = ctk.CTkFrame(chk_frame, fg_color="transparent")
            r.grid(row=row, column=0, sticky="ew", padx=14, pady=6)
            r.grid_columnconfigure(1, weight=1)
            ctk.CTkCheckBox(r, text=label, variable=var,
                            font=("Consolas", 12, "bold"),
                            text_color=controller.TEXT_SUB,
                            checkmark_color="white",
                            fg_color=controller.NEON_RED, hover_color=controller.HOVER_RED
                            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(r, text=desc, font=("Consolas", 10),
                         text_color=controller.TEXT_GRAY).grid(row=1, column=0, sticky="w", padx=26)

        _nav(self, controller, "DestinationPage",
             next_fn=lambda: controller.show_frame("StartMenuPage"))


# =============================================================================
# PAGE 5 – Select Start Menu Folder
# =============================================================================
class StartMenuPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        _banner(self, "Step 5 of 7", "Select Start Menu Folder")

        ctk.CTkLabel(
            self,
            text="Setup will create the program's shortcuts in the following\n"
                 "Start Menu folder. You can enter a different name below.",
            font=("Consolas", 12), text_color=controller.TEXT_SUB, justify="left"
        ).grid(row=1, column=0, padx=30, pady=(18, 12), sticky="w")

        self._sm_var = ctk.StringVar(value=_APP_TITLE)
        ctk.CTkEntry(
            self, textvariable=self._sm_var,
            font=("Consolas", 12), width=400,
            fg_color=controller.ENTRY_BG, border_color=controller.BORDER_RED
        ).grid(row=2, column=0, padx=30, sticky="w")

        _nav(self, controller, "ComponentsPage",
             next_fn=lambda: controller.show_frame("AdditionalTasksPage"))

    def get_folder_name(self) -> str:
        return self._sm_var.get().strip() or _APP_TITLE


# =============================================================================
# PAGE 6 – Additional Tasks
# =============================================================================
class AdditionalTasksPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        _banner(self, "Step 6 of 7", "Select Additional Tasks")

        ctk.CTkLabel(
            self,
            text="Select any additional tasks you would like Setup to perform\n"
                 "while installing CSM, then click Next.",
            font=("Consolas", 12), text_color=controller.TEXT_SUB, justify="left"
        ).grid(row=1, column=0, padx=30, pady=(18, 14), sticky="w")

        box = ctk.CTkFrame(self, fg_color=controller.ENTRY_BG,
                           corner_radius=6, border_width=1,
                           border_color=controller.BORDER_RED)
        box.grid(row=2, column=0, padx=30, sticky="ew")

        self.var_boot = ctk.BooleanVar(value=True)
        r = ctk.CTkFrame(box, fg_color="transparent")
        r.grid(row=0, column=0, sticky="ew", padx=14, pady=8)
        ctk.CTkCheckBox(
            r, text="Launch CSM automatically on system boot (Recommended)",
            variable=self.var_boot,
            font=("Consolas", 12),
            text_color=controller.TEXT_SUB,
            checkmark_color="white",
            fg_color=controller.NEON_RED, hover_color=controller.HOVER_RED
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            r,
            text="Adds a startup registry entry so CSM runs silently in the background.",
            font=("Consolas", 10), text_color=controller.TEXT_GRAY
        ).grid(row=1, column=0, sticky="w", padx=26)

        _nav(self, controller, "StartMenuPage",
             next_fn=lambda: controller.show_frame("ReadyPage"))


# =============================================================================
# PAGE 7 – Ready to Install
# =============================================================================
class ReadyPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._controller = controller

        _banner(self, "Step 7 of 7", "Ready to Install")

        ctk.CTkLabel(
            self,
            text="Setup is now ready to install CSM on your computer.\n\n"
                 "Click Install to proceed, or Back to review or change any settings.",
            font=("Consolas", 13), text_color=controller.TEXT_SUB, justify="left"
        ).grid(row=1, column=0, padx=30, pady=18, sticky="w")

        # Summary box
        self.summary = ctk.CTkTextbox(
            self, font=("Consolas", 11), text_color=controller.TEXT_SUB,
            fg_color=controller.ENTRY_BG, border_color=controller.BORDER_RED,
            border_width=1, wrap="word", state="disabled"
        )
        self.summary.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 6))

        sep = ctk.CTkFrame(self, height=1, fg_color=controller.BORDER_RED)
        sep.grid(row=98, column=0, sticky="ew", padx=0, pady=(10, 0))

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=99, column=0, sticky="ew", padx=20, pady=10)
        nav.grid_columnconfigure(0, weight=1)
        
        neon_red = ("#CC0000", "#FF3333")
        text_main = ("#1A1A1A", "#CCCCCC")
        hover_red = ("#FFEEEE", "#5A0000")

        ctk.CTkButton(
            nav, text="< Back", width=100,
            fg_color="transparent", border_width=1,
            border_color=controller.BORDER_RED, text_color=text_main,
            command=lambda: controller.show_frame("AdditionalTasksPage")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            nav, text="Install", width=130,
            fg_color=hover_red, border_width=2, border_color=neon_red, 
            hover_color=hover_red, text_color=neon_red, font=("Consolas", 13, "bold"),
            command=controller.execute_installation
        ).grid(row=0, column=1, sticky="e")

    def tkraise(self, aboveThis=None):
        """Refresh summary when this page is raised."""
        super().tkraise(aboveThis)
        ctrl = self._controller
        comp = ctrl.frames["ComponentsPage"]
        sm   = ctrl.frames["StartMenuPage"]
        add  = ctrl.frames["AdditionalTasksPage"]
        dest = ctrl.frames["DestinationPage"]

        lines = [
            f"Destination:    {dest.get_path()}",
            f"Desktop icon:   {'Yes' if comp.var_desktop.get() else 'No'}",
            f"Start Menu:     {'Yes – ' + sm.get_folder_name() if comp.var_startmenu.get() else 'No'}",
            f"Autostart:      {'Yes' if add.var_boot.get() else 'No'}",
        ]
        self.summary.configure(state="normal")
        self.summary.delete("1.0", "end")
        self.summary.insert("end", "\n".join(lines))
        self.summary.configure(state="disabled")


# =============================================================================
# PROGRESS / UNINSTALL PAGE (not a wizard step – shown during operations)
# =============================================================================
class ProgressPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        self.header_lbl = ctk.CTkLabel(
            self, text="Installing...",
            font=("Consolas", 18, "bold"), text_color=controller.NEON_RED
        )
        self.header_lbl.grid(row=0, column=0, pady=(60, 16))

        self.progress = ctk.CTkProgressBar(self, width=460, height=18, progress_color=controller.NEON_RED)
        self.progress.grid(row=1, column=0, pady=6)
        self.progress.set(0)

        self.log_lbl = ctk.CTkLabel(
            self, text="Preparing...",
            font=("Consolas", 11), text_color=controller.TEXT_GRAY
        )
        self.log_lbl.grid(row=2, column=0, pady=14)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="e", padx=30, pady=(40, 0))

        self.btn_finish = ctk.CTkButton(
            btn_row, text="Finish", width=120,
            fg_color=controller.HOVER_RED, border_width=2, border_color=controller.NEON_RED,
            hover_color=controller.PANEL_BG, text_color=controller.NEON_RED,
            font=("Consolas", 13, "bold"), state="disabled"
        )
        self.btn_finish.grid(row=0, column=0)

    def set_status(self, text: str, progress: float):
        self.log_lbl.configure(text=text)
        self.progress.set(progress)
        self.update()


# =============================================================================
# Entry points
# =============================================================================
def trigger_installer(current_exe_path: str):
    """Launch the installer wizard. Called from main.py on first run."""
    app = ProfessionalInstaller(current_exe_path)
    app.mainloop()
