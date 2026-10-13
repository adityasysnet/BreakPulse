import pystray
from PIL import Image
import threading
import os
from typing import Callable, Optional

class TrayManager:
    def __init__(
        self,
        icon_path: str,
        on_show_main: Callable[[], None],
        on_toggle_timer: Callable[[], None],
        on_skip: Callable[[], None],
        on_quit: Callable[[], None]
    ):
        self.icon_path = icon_path
        self.on_show_main = on_show_main
        self.on_toggle_timer = on_toggle_timer
        self.on_skip = on_skip
        self.on_quit = on_quit

        self.tray_icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if not os.path.exists(self.icon_path):
            # Create a simple fallback in-memory image
            img = Image.new("RGB", (64, 64), color=(16, 185, 129))
        else:
            img = Image.open(self.icon_path)

        menu = pystray.Menu(
            pystray.MenuItem("🌿 BreakPulse", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Window", self._on_show_clicked, default=True),
            pystray.MenuItem("Play / Pause", self._on_toggle_clicked),
            pystray.MenuItem("Skip Phase", self._on_skip_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._on_quit_clicked)
        )

        self.tray_icon = pystray.Icon("BreakPulse", img, "BreakPulse - Active", menu)
        self._thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self._thread.start()

    def update_tooltip(self, text: str):
        if self.tray_icon:
            self.tray_icon.title = f"BreakPulse: {text}"

    def _on_show_clicked(self, icon=None, item=None):
        self.on_show_main()

    def _on_toggle_clicked(self, icon=None, item=None):
        self.on_toggle_timer()

    def _on_skip_clicked(self, icon=None, item=None):
        self.on_skip()

    def _on_quit_clicked(self, icon=None, item=None):
        self.stop()
        self.on_quit()

    def stop(self):
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
