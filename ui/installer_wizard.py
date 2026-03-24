import sys
import os
import shutil
import platform
import winreg
import subprocess
import time
import customtkinter as ctk
from pathlib import Path
from core.config import resource_path

class ProfessionalInstaller(ctk.CTk):
    def __init__(self, current_exe_path):
        super().__init__()
        self.current_exe = current_exe_path
        self.install_dir = Path(os.environ.get("LOCALAPPDATA")) / "iMazK_CSM"
        
        # Configure matching Setup Dimensions giving enough room for Next buttons
        self.title("iMazK pvt ltd - CSM Setup")
        self.geometry("600x450")
        self.resizable(False, False)
        
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass

        # Container for pages to allow stacking
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        
        # Build the sequence arrays
        for F in (WelcomePage, OptionsPage, ProgressPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            # stack all pages in the exact same spot natively
            frame.grid(row=0, column=0, sticky="nsew")

        # Raise Welcome natively
        self.show_frame("WelcomePage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def execute_uninstall(self):
        """Silently strips all registry and shortcut dependencies, then stages a batch script to delete the .exe"""
        self.frames["ProgressPage"].header_lbl.configure(text="Uninstalling CSM...")
        self.show_frame("ProgressPage")
        self.update()

        # 1. Cleanup Registry Native Lock
        try:
            registry_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(reg_key, "ClipboardSecurityManager")
            winreg.CloseKey(reg_key)
        except Exception:
            pass

        # 2. Cleanup Native Shortcuts
        desktop = Path(os.environ.get("USERPROFILE")) / "Desktop" / "CSM Dashboard.lnk"
        start_menu = Path(os.environ.get("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "CSM Dashboard.lnk"
        uninstaller = Path(os.environ.get("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Uninstall CSM.lnk"
        
        for path in [desktop, start_menu, uninstaller]:
            if path.exists():
                try:
                    os.remove(str(path))
                except: pass

        # 3. Stage Self-Deletion Script
        from core import auth
        from core.config import CSM_DATA_DIR
        
        # Completely burn the local database logs and Keyring credentials off the Hard-Drive!
        auth.delete_all_credentials()
        try:
            shutil.rmtree(CSM_DATA_DIR, ignore_errors=True)
        except:
            pass
            
        try:
            shutil.rmtree(str(self.install_dir), ignore_errors=True)
        except:
            pass
            
        self.frames["ProgressPage"].log_lbl.configure(text="Uninstallation Successful.\nYou may close this window and delete this setup file.")
        self.frames["ProgressPage"].progress.set(1.0)
        self.frames["ProgressPage"].btn_finish.configure(state="normal", text="Close", command=lambda: sys.exit(0))
        self.update()


    def execute_installation(self):
        """Processes the exact payload copying mirroring NSIS/VLC setups"""
        options = self.frames["OptionsPage"]
        prog = self.frames["ProgressPage"]
        
        self.show_frame("ProgressPage")
        self.update()

        prog.log_lbl.configure(text="Extracting files to AppData directory...")
        self.install_dir.mkdir(parents=True, exist_ok=True)
        target_exe = self.install_dir / "ClipboardSecurityManager.exe"

        time.sleep(0.5) 
        prog.progress.set(0.3)
        self.update()

        try:
            shutil.copy2(self.current_exe, target_exe)
        except Exception as e:
            pass

        prog.log_lbl.configure(text="Registering Native Shortcuts...")
        time.sleep(0.5)
        prog.progress.set(0.6)
        self.update()

        # Powershell mapping
        ps_script = f"""
        $TargetFile = "{target_exe}"
        $IconFile = "{target_exe}"
        $WshShell = New-Object -comObject WScript.Shell
        """
        
        if options.var_desktop.get():
            desktop = Path(os.environ.get("USERPROFILE")) / "Desktop" / "CSM Dashboard.lnk"
            ps_script += f"""
            $Shortcut = $WshShell.CreateShortcut("{desktop}")
            $Shortcut.TargetPath = $TargetFile
            $Shortcut.IconLocation = $IconFile
            $Shortcut.WorkingDirectory = "{self.install_dir}"
            $Shortcut.Save()
            """
            
        if options.var_start.get():
            start_menu = Path(os.environ.get("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "CSM Dashboard.lnk"
            ps_script += f"""
            $Shortcut = $WshShell.CreateShortcut("{start_menu}")
            $Shortcut.TargetPath = $TargetFile
            $Shortcut.IconLocation = $IconFile
            $Shortcut.WorkingDirectory = "{self.install_dir}"
            $Shortcut.Save()
            """
            
            # Map the uninstaller cleanly directly inside the start menu
            uninstaller = Path(os.environ.get("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Uninstall CSM.lnk"
            ps_script += f"""
            $Shortcut = $WshShell.CreateShortcut("{uninstaller}")
            $Shortcut.TargetPath = $TargetFile
            $Shortcut.Arguments = "--uninstall"
            $Shortcut.IconLocation = $IconFile
            $Shortcut.WorkingDirectory = "{self.install_dir}"
            $Shortcut.Save()
            """

        with open(self.install_dir / "setup.ps1", "w") as f:
            f.write(ps_script)
            
        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(self.install_dir / "setup.ps1")], creationflags=subprocess.CREATE_NO_WINDOW)

        prog.log_lbl.configure(text="Configuring OS Autoloader...")
        time.sleep(0.5)
        prog.progress.set(0.8)
        self.update()

        # Launch background process on Boot mapping via Registry
        if options.var_boot.get():
            try:
                registry_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(reg_key, "ClipboardSecurityManager", 0, winreg.REG_SZ, str(target_exe))
                winreg.CloseKey(reg_key)
            except Exception as e:
                pass
                
        prog.log_lbl.configure(text="Installation Complete!\nStarting Application...")
        prog.progress.set(1.0)
        self.update()

        subprocess.Popen([str(target_exe)])
        sys.exit(0)


class WelcomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(self, text="Welcome to the Clipboard Security\nManager Setup Wizard", font=("Consolas", 20, "bold"), text_color=("#171925", "#d83b3c"))
        title.grid(row=0, column=0, pady=(40, 20))
        
        desc = ctk.CTkLabel(self, text="This wizard will guide you through the installation of CSM.\n\nIt is recommended that you close all other native cryptography\napplications before starting Setup.", font=("Consolas", 14), text_color=("#333333", "#c8cad6"), justify="left")
        desc.grid(row=1, column=0, pady=(0, 40))
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", pady=(40, 20), padx=40)
        # Push next button to the right cleanly
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        # Detect previous installation natively
        if controller.install_dir.exists():
            btn_un = ctk.CTkButton(btn_frame, text="Uninstall Existing", width=140, fg_color="#FF5555", hover_color="#AA0000", command=controller.execute_uninstall)
            btn_un.grid(row=0, column=0, sticky="w")
        else:
            # Spacer label so col 1 stays right
            ctk.CTkLabel(btn_frame, text="").grid(row=0, column=0)
            
        btn_next = ctk.CTkButton(btn_frame, text="Next >", width=120, command=lambda: controller.show_frame("OptionsPage"))
        btn_next.grid(row=0, column=1, sticky="e")


class OptionsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(self, text="Choose Components", font=("Consolas", 18, "bold"), text_color=("#171925", "#d83b3c"))
        title.grid(row=0, column=0, pady=(30, 10))

        sub = ctk.CTkLabel(self, text="Check the features you want to install natively.", font=("Consolas", 12))
        sub.grid(row=1, column=0, pady=(0, 20))

        self.var_desktop = ctk.BooleanVar(value=True)
        chk_desktop = ctk.CTkCheckBox(self, text="Create Desktop Shortcut", variable=self.var_desktop, font=("Consolas", 14))
        chk_desktop.grid(row=2, column=0, sticky="w", padx=100, pady=10)

        self.var_start = ctk.BooleanVar(value=True)
        chk_start = ctk.CTkCheckBox(self, text="Create Start Menu Entry (Includes Uninstaller)", variable=self.var_start, font=("Consolas", 14))
        chk_start.grid(row=3, column=0, sticky="w", padx=100, pady=10)

        self.var_boot = ctk.BooleanVar(value=True)
        chk_boot = ctk.CTkCheckBox(self, text="Launch CSM on System Boot (Recommended)", variable=self.var_boot, font=("Consolas", 14))
        chk_boot.grid(row=4, column=0, sticky="w", padx=100, pady=10)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, sticky="ew", pady=(60, 20), padx=40)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)

        btn_back = ctk.CTkButton(btn_frame, text="< Back", width=100, fg_color="transparent", border_width=1, command=lambda: controller.show_frame("WelcomePage"))
        btn_back.grid(row=0, column=0, sticky="w")

        btn_next = ctk.CTkButton(btn_frame, text="Install", width=120, command=controller.execute_installation)
        btn_next.grid(row=0, column=2, sticky="e")


class ProgressPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        self.header_lbl = ctk.CTkLabel(self, text="Installing...", font=("Consolas", 18, "bold"), text_color=("#171925", "#d83b3c"))
        self.header_lbl.grid(row=0, column=0, pady=(60, 20))

        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.grid(row=1, column=0, pady=10)
        self.progress.set(0)

        self.log_lbl = ctk.CTkLabel(self, text="Initializing...", font=("Consolas", 12), text_color=("#555555", "#8a8d9e"))
        self.log_lbl.grid(row=2, column=0, pady=20)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", pady=(60, 20), padx=40)
        btn_frame.grid_columnconfigure(0, weight=1)

        self.btn_finish = ctk.CTkButton(btn_frame, text="Next >", width=120, state="disabled")
        self.btn_finish.grid(row=0, column=0, sticky="e")


def trigger_installer(current_exe_path):
    app = ProfessionalInstaller(current_exe_path)
    app.mainloop()
