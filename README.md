# ⚡ BreakPulse

> **Intelligent Break Reminder, Eye Strain Guard & Ergonomic Pomodoro Desktop App for Windows.**

A high-performance Windows desktop application that combines the **Pomodoro technique**, **optometrist-backed 20-20-20 eye strain care**, **guided box breathing**, **interactive desk stretches**, and **strict full-screen break enforcement** into a unified, sleek dark-mode desktop companion.

---

## ✨ Key Features

- **⏱️ Flexible Pomodoro Engine:**
  - Classic 25m/5m cycles, 50m Deep Work cycles, or fully customizable intervals.
  - Automatically schedules Long Rest (15m+) after your desired number of sessions.
- **👁️ 20-20-20 Eye Strain Protection:**
  - Micro-break reminders (every 20 minutes, 20 seconds of distance rest) to prevent digital eye fatigue and headaches.
- **🛡️ Strict vs. Gentle Break Enforcement:**
  - **Strict Mode:** Frosted, full-screen overlay lock with countdown timer, breathing exercises, and an emergency bypass with delay.
  - **Gentle Mode:** Subtle audio chimes and badge alerts without taking over your display.
- **🫁 Interactive Box Breathing Visualizer:**
  - Real-time animated canvas guiding you through 4-4-4-4 rhythm (*Inhale -> Hold -> Exhale -> Hold*) to rapidly de-stress.
- **🧘 Ergonomic Desk Stretches:**
  - Built-in illustrated exercises for neck release, overhead spine extension, and wrist/forearm carpal-tunnel prevention.
- **💧 Hydration Tracker:**
  - Quick-log water intake with daily goal progress.
- **💤 AFK & Idle Detection:**
  - Calls native Windows `GetLastInputInfo` to automatically pause the timer when you step away from your computer so you don't lose your session.
- **📌 Always-On-Top Mini HUD Widget:**
  - Compact, draggable floating pill that docks in the corner of your screen showing real-time timer status and quick playback controls.
- **🔔 Windows System Tray Integration:**
  - Minimizes cleanly to the Windows notification tray with right-click menu controls (*Start, Pause, Skip, Exit*).
- **🎵 Zero-Dependency Acoustic Chimes:**
  - Pure in-memory synthesized harmonic bells using Windows `winsound`—no external audio files or codecs needed.
- **📋 Integrated Focus Tasks & Goal Tracking:**
  - Plan work objectives with estimated Pomodoro targets (`🍅 1/3`).
  - Active goal indicators and automatic pomodoro completion logging.
- **🎧 Real-Time Ambient Soundscapes:**
  - In-memory synthesized Brown Noise, Soothing Rain, Soft White Noise, and Lofi Clock Ticks to drown out distractions and lock into deep cognitive flow.
- **⌨️ Global Windows Hotkeys:**
  - Control your timer hands-free from anywhere (even when minimized in tray):
    - `Ctrl + Alt + Space`: Play / Pause Focus
    - `Ctrl + Alt + S`: Skip to Next Phase
    - `Ctrl + Alt + M`: Toggle Mini HUD
    - `Ctrl + Alt + B`: Instant 1-Min Rest
- **📈 7-Day Visual Activity Bar Chart:**
  - Interactive activity graph showing daily focus minutes over the past week.
- **📥 One-Click CSV Timesheet Export:**
  - Export complete historical records (date, focus hours, sessions, breaks honored) for timesheets or productivity auditing.
- **🎨 Dynamic Light & Dark Theme Switcher:**
  - One-click toggle in the header (`☀️ Light` / `🌙 Dark`) with persistent theme saving and full system-theme sync.
- **✨ Premium "Outfit" Google Font Typography:**
  - Bundled and registered in-memory at launch using native Windows GDI (`AddFontResourceExW`) for a sleek, modern, high-contrast aesthetic without needing system installation.
- **📊 Daily Insights & Streaks:**
  - Tracks total daily focus hours, completed Pomodoros, break compliance percentage, and consecutive daily streaks.

---

## 🚀 Quick Start (Development)

This project uses [`uv`](https://github.com/astral-sh/uv) for ultra-fast dependency resolution and virtual environments.

### 1. Prerequisites
- Windows 10/11
- Python 3.12+
- `uv` installed (`winget install astral-sh.uv` or `pip install uv`)

### 2. Setup & Run
```bash
# Clone the repository
git clone https://github.com/adityasysnet/BreakPulse.git
cd BreakPulse

# Install dependencies with uv
uv sync

# Run BreakPulse
uv run python main.py
```

---

## 📦 Building Standalone Single-File `.exe`

To build an independent executable that runs without Python:

```bash
uv add --dev pyinstaller
uv run python build.py
```
The standalone binary will be generated at `dist/BreakPulse.exe`.

---

## 🛠️ Project Structure

```
BreakPulse/
├── src/
│   ├── audio_manager.py     # In-memory harmonic chime synthesizer
│   ├── config_manager.py    # Settings persistence (data/config.json)
│   ├── mini_widget.py       # Draggable floating HUD widget
│   ├── overlay_window.py    # Full-screen break lock & breathing canvas
│   ├── stats_manager.py     # Daily focus time, streaks & hydration tracking
│   ├── timer_engine.py      # Core Pomodoro, eye break & idle state machine
│   └── tray_manager.py      # Windows notification tray integration
├── data/                    # User data and configuration storage (offline)
├── build.py                 # PyInstaller standalone compilation script
├── generate_assets.py       # Icon generator (PNG & ICO multi-resolution)
├── icon.ico                 # App icon
├── icon.png                 # App icon
├── main.py                  # Desktop application entry point
├── pyproject.toml           # uv project configuration
└── README.md                # Documentation
```

---

## 🛡️ License
MIT License. Free for personal and commercial productivity use.
