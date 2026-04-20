import pystray
from PIL import Image, ImageDraw
import threading
from ui import dashboard
from core.config import resource_path
import os

class TrayApp:
    def __init__(self, clipboard_monitor):
        """Initializes the background taskbar watcher managing System interactions."""
        self.monitor = clipboard_monitor
        self.icon = None

    def create_icon_image(self, active=True):
        """Loads physical asset natively bypassing algorithm fallback!"""
        try:
            img = Image.open(resource_path("icon.ico"))
            # Optional: Apply visual grayscale math to visually signal the application is offline
            if not active:
                img = img.convert('L')
            return img
        except Exception:
            # Fallback
            color = (0, 255, 255) if active else (255, 0, 0)
            img = Image.new('RGB', (64, 64), color='black')
            draw = ImageDraw.Draw(img)
            draw.rectangle((16, 24, 48, 56), fill=color, outline="white")
            draw.arc((16, 8, 48, 40), 180, 0, fill="white", width=4)
            return img


    def switch_protection(self, icon, item):
        """Disables or enables the asynchronous copying hooks."""
        if self.monitor.running:
            self.monitor.stop_monitoring()
            self.icon.icon = self.create_icon_image(active=False)
        else:
            self.monitor.start_monitoring()
            self.icon.icon = self.create_icon_image(active=True)

    def open_dashboard(self, icon, item):
        """Boots the primary CustomTkinter ui interface on a dedicated thread."""
        threading.Thread(target=dashboard.launch_dashboard, daemon=True).start()

    def exit_app(self, icon, item):
        """Shutdown."""
        self.monitor.stop_monitoring()
        icon.stop()
        os._exit(0)

    def run(self):
        """Runs the loop indefinitely."""
        menu = pystray.Menu(
            pystray.MenuItem('Open Dashboard', self.open_dashboard),
            pystray.MenuItem('Toggle Protection', self.switch_protection),
            pystray.MenuItem('Exit CSM', self.exit_app)
        )
        
        self.icon = pystray.Icon("CSM", self.create_icon_image(active=True), "Clipboard Security Manager", menu)
        self.icon.run()
