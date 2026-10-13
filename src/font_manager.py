import os
import sys
import ctypes

FONT_FAMILY = "Outfit"

def register_custom_fonts():
    """
    Registers bundled TTF fonts into the current Windows process session
    using AddFontResourceExW (FR_PRIVATE). No admin rights needed.
    """
    if sys.platform != "win32":
        return

    # Check for PyInstaller _MEIPASS or local directory
    if hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.abspath(".")

    font_path = os.path.join(base_dir, "assets", "fonts", "Outfit-VariableFont_wght.ttf")
    if os.path.exists(font_path):
        try:
            FR_PRIVATE = 0x10
            res = ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
            if res > 0:
                print(f"[FontManager] Loaded {res} font resources from Outfit.")
        except Exception as e:
            print(f"[FontManager] Failed to register font: {e}")
