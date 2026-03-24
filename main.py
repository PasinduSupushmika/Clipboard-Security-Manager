import sys
import os
from pathlib import Path
from core import database, auth
from core.clipboard_manager import ClipboardMonitor
from ui import setup_wizard, auth_dialog, tray_icon

def start_application():
    """Primary execution pipeline initializing resources synchronously prior to asynchronous bootloaders."""
    
    # Check if a user clicked "Uninstall CSM" from the native Windows shortcut menu
    if "--uninstall" in sys.argv:
        print("[SETUP] Uninstall parameter detected. Booting native uninstaller phase.")
        from ui import installer_wizard
        app = installer_wizard.ProfessionalInstaller(sys.executable)
        # Force to Progress and strip assets
        app.execute_uninstall()
        app.mainloop()
        sys.exit(0)
    
    # 0. Check if we need to run the Enterprise Installer instead
    # This detects if PyInstaller compiled us, AND if we are not running from the installed directory
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen and "iMazK_CSM" not in str(sys.executable):
        print("[SETUP] First execution detected off-site. Launching Setup Payload.")
        from ui import installer_wizard
        installer_wizard.trigger_installer(sys.executable)
        sys.exit(0)
    
    # 1. Database Pruning and Tables Setup
    try:
        database.init_db()
        database.purge_old_logs()
    except Exception as e:
        print(f"[FATAL] Database Pipeline Fault: {e}")
        sys.exit(1)

    # 2. Keyring Enclave Check
    if not auth.is_setup_complete():
        print("[INIT] Operating System Master Password Keyring unset. Booting GUI Dialog.")
        setup_wizard.run_wizard()
        
        # Second verification post-wizard termination 
        if not auth.is_setup_complete():
            print("[EXIT] Password Configuration Aborted. System Terminating safely.")
            sys.exit(0)

    # 3. Instantiate Asynchronous Interceptor Engines
    try:
        # We pass the dynamic CustomTkinter Auth Prompt popup as our native boolean check
        monitor = ClipboardMonitor(paste_callback=auth_dialog.request_authorization)
        monitor.start_monitoring()
        print("[ONLINE] AES-256-GCM Clipboard Securer Active.")
    except Exception as e:
        print(f"[FATAL] Clipboard Native Hook API Error: {e}")
        sys.exit(1)

    # 4. Bind the System taskbar Icon interface 
    # Must explicitly run natively on main thread
    app_tray = tray_icon.TrayApp(monitor)
    app_tray.run()


if __name__ == "__main__":
    start_application()
