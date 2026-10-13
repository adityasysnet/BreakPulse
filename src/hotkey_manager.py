import ctypes
from ctypes import wintypes
import threading
import sys
from typing import Callable, Optional

# Win32 Constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

VK_SPACE = 0x20
VK_S = 0x53
VK_M = 0x4D
VK_B = 0x42

class HotkeyManager:
    """
    Native Windows Global Hotkeys without third-party drivers or admin rights.
    Keybindings:
      - Ctrl + Alt + Space: Play / Pause Focus Timer
      - Ctrl + Alt + S: Skip phase
      - Ctrl + Alt + M: Toggle Mini HUD Widget
      - Ctrl + Alt + B: Instant Micro-Break
    """
    def __init__(
        self,
        on_toggle_timer: Optional[Callable[[], None]] = None,
        on_skip: Optional[Callable[[], None]] = None,
        on_toggle_mini: Optional[Callable[[], None]] = None,
        on_instant_break: Optional[Callable[[], None]] = None
    ):
        self.on_toggle_timer = on_toggle_timer
        self.on_skip = on_skip
        self.on_toggle_mini = on_toggle_mini
        self.on_instant_break = on_instant_break

        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if sys.platform != "win32":
            return
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._msg_loop, daemon=True)
        self._thread.start()

    def _msg_loop(self):
        user32 = ctypes.windll.user32
        mods = MOD_CONTROL | MOD_ALT | MOD_NOREPEAT

        # Register hotkeys (id 1..4)
        user32.RegisterHotKey(None, 1, mods, VK_SPACE)
        user32.RegisterHotKey(None, 2, mods, VK_S)
        user32.RegisterHotKey(None, 3, mods, VK_M)
        user32.RegisterHotKey(None, 4, mods, VK_B)

        msg = wintypes.MSG()
        while self.running:
            # GetMessage blocks until a Windows message arrives
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break

            if msg.message == WM_HOTKEY:
                hotkey_id = msg.wParam
                if hotkey_id == 1 and self.on_toggle_timer:
                    self.on_toggle_timer()
                elif hotkey_id == 2 and self.on_skip:
                    self.on_skip()
                elif hotkey_id == 3 and self.on_toggle_mini:
                    self.on_toggle_mini()
                elif hotkey_id == 4 and self.on_instant_break:
                    self.on_instant_break()

        # Clean up
        user32.UnregisterHotKey(None, 1)
        user32.UnregisterHotKey(None, 2)
        user32.UnregisterHotKey(None, 3)
        user32.UnregisterHotKey(None, 4)

    def stop(self):
        self.running = False
        if sys.platform == "win32":
            ctypes.windll.user32.PostQuitMessage(0)
