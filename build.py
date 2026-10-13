"""
Build script to compile BreakPulse into a standalone, single-file Windows executable (.exe).
Usage:
    uv run python build.py
"""

import subprocess
import sys
import os

def build_exe():
    print("[*] Starting BreakPulse PyInstaller compilation...")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name", "BreakPulse",
        "--icon", "icon.ico",
        "--add-data", "icon.ico;.",
        "--add-data", "icon.png;.",
        "--add-data", "logo_32.png;.",
        "--add-data", "assets;assets",
        "--collect-all", "customtkinter",
        "--collect-all", "pystray",
        "--collect-all", "PIL",
        "--collect-submodules", "src",
        "main.py"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n[+] Build complete! Executable generated at: dist/BreakPulse.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n[-] Build failed with exit code: {e.returncode}")

if __name__ == "__main__":
    build_exe()
