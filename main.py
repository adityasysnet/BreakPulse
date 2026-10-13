import os
import sys
import threading
import time
import customtkinter as ctk
from PIL import Image
from tkinter import filedialog, messagebox

# Import internal modules
from src.config_manager import ConfigManager
from src.stats_manager import StatsManager
from src.audio_manager import AudioManager
from src.soundscapes import SoundscapesManager
from src.task_manager import TaskManager
from src.hotkey_manager import HotkeyManager
from src.timer_engine import TimerEngine, TimerState
from src.overlay_window import BreakOverlayWindow
from src.mini_widget import MiniWidget
from src.tray_manager import TrayManager
from src.font_manager import register_custom_fonts, FONT_FAMILY

APP_NAME = "BreakPulse"
APP_VERSION = "1.0.0"
FONT_NAME = FONT_FAMILY

def get_asset_path(relative_path: str) -> str:
    """Gets absolute path to resources."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class BreakPulseApp(ctk.CTk):
    def __init__(self):
        # 1. Register Outfit Font into Windows GDI before rendering UI
        register_custom_fonts()

        super().__init__()

        # 2. Initialize Managers
        self.config = ConfigManager()
        self.stats = StatsManager()
        self.audio = AudioManager(enabled=self.config.get("sound_enabled", True))
        self.soundscapes = SoundscapesManager()
        self.tasks = TaskManager()
        self.engine = TimerEngine(self.config, self.stats)

        # 3. Theme & Window Setup
        initial_mode = self.config.get("appearance_mode", "dark")
        ctk.set_appearance_mode(initial_mode)
        ctk.set_default_color_theme("green")

        self.title(f"{APP_NAME} • Intelligent Pomodoro & Health Guard")
        self.geometry("680x790")
        self.minsize(620, 720)

        self.icon_path = get_asset_path("icon.ico")
        if os.path.exists(self.icon_path):
            try:
                self.iconbitmap(self.icon_path)
            except Exception:
                pass

        # Windows and sub-windows references
        self.overlay_window: BreakOverlayWindow = None
        self.mini_widget: MiniWidget = None

        # 4. Setup Callbacks
        self.engine.on_tick = self._on_timer_tick
        self.engine.on_state_change = self._on_timer_state_change
        self.engine.on_idle_pause = self._on_idle_pause
        self.engine.on_session_completed = self._on_focus_session_finished

        # 5. Setup UI
        self._setup_ui()

        # 6. Global Hotkeys Setup
        if self.config.get("global_hotkeys_enabled", True):
            self.hotkeys = HotkeyManager(
                on_toggle_timer=lambda: self.after(0, self._handle_play_pause),
                on_skip=lambda: self.after(0, self._handle_skip),
                on_toggle_mini=lambda: self.after(0, self.toggle_mini_widget),
                on_instant_break=lambda: self.after(0, self.engine.start_eye_break)
            )
            self.hotkeys.start()
        else:
            self.hotkeys = None

        # 7. Setup Tray Icon
        self.tray = TrayManager(
            icon_path=get_asset_path("icon.png"),
            on_show_main=self.show_main_window,
            on_toggle_timer=self._handle_play_pause,
            on_skip=self._handle_skip,
            on_quit=self.quit_app
        )
        self.tray.start()

        # Window closing protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close_requested)

    def _setup_ui(self):
        # Header Bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 8))

        # Title & Brand Logo
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        logo_path = get_asset_path("logo_32.png")
        if os.path.exists(logo_path):
            try:
                self.logo_img_pil = Image.open(logo_path)
                self.header_logo = ctk.CTkImage(
                    light_image=self.logo_img_pil,
                    dark_image=self.logo_img_pil,
                    size=(26, 26)
                )
                logo_lbl = ctk.CTkLabel(title_box, image=self.header_logo, text="")
                logo_lbl.pack(side="left", padx=(0, 8))
            except Exception:
                pass

        app_title = ctk.CTkLabel(
            title_box,
            text=APP_NAME,
            font=ctk.CTkFont(family=FONT_NAME, size=24, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        app_title.pack(side="left")

        ver_badge = ctk.CTkLabel(
            title_box,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(family=FONT_NAME, size=11, weight="bold"),
            text_color=("#475569", "#94A3B8"),
            fg_color=("#E2E8F0", "#0F172A"),
            corner_radius=8,
            padx=8,
            pady=2
        )
        ver_badge.pack(side="left", padx=(10, 0))

        # Header Right Controls (Theme Switcher, Mini Widget)
        h_right = ctk.CTkFrame(header, fg_color="transparent")
        h_right.pack(side="right")

        # ☀️ / 🌙 Theme Toggle Button
        is_dark = (ctk.get_appearance_mode().lower() == "dark")
        self.btn_theme = ctk.CTkButton(
            h_right,
            text="☀️ Light" if is_dark else "🌙 Dark",
            width=88,
            height=30,
            font=ctk.CTkFont(family=FONT_NAME, size=12, weight="bold"),
            fg_color=("#E2E8F0", "#1E293B"),
            hover_color=("#CBD5E1", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            corner_radius=15,
            command=self.toggle_appearance_mode
        )
        self.btn_theme.pack(side="left", padx=4)

        self.btn_mini = ctk.CTkButton(
            h_right,
            text="📌 Mini HUD",
            width=92,
            height=30,
            font=ctk.CTkFont(family=FONT_NAME, size=12, weight="bold"),
            fg_color=("#E2E8F0", "#1E293B"),
            hover_color=("#CBD5E1", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            corner_radius=15,
            command=self.toggle_mini_widget
        )
        self.btn_mini.pack(side="left", padx=4)

        # Tabview
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=("#F1F5F9", "#0F172A"),
            segmented_button_fg_color=("#E2E8F0", "#1E293B"),
            segmented_button_selected_color="#10B981",
            segmented_button_selected_hover_color="#059669",
            corner_radius=16
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(2, 14))

        self.tab_timer = self.tabview.add("⏱️ Focus & Tasks")
        self.tab_soundscapes = self.tabview.add("🎧 Soundscapes")
        self.tab_wellness = self.tabview.add("🧘 Wellness & Rest")
        self.tab_stats = self.tabview.add("📊 Analytics & Reports")
        self.tab_settings = self.tabview.add("⚙️ Settings")

        self._build_timer_tab()
        self._build_soundscapes_tab()
        self._build_wellness_tab()
        self._build_stats_tab()
        self._build_settings_tab()

    # ================= ⏱️ FOCUS & TASKS TAB =================
    def _build_timer_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_timer, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=4, pady=4)

        # Main Countdown Card
        card = ctk.CTkFrame(
            container,
            corner_radius=18,
            fg_color=("#FFFFFF", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        card.pack(fill="x", pady=6)

        # Status Badge Indicator
        self.status_badge = ctk.CTkLabel(
            card,
            text="● READY TO FOCUS",
            font=ctk.CTkFont(family=FONT_NAME, size=13, weight="bold"),
            text_color=("#475569", "#94A3B8"),
            fg_color=("#F1F5F9", "#0F172A"),
            corner_radius=20,
            padx=16,
            pady=5
        )
        self.status_badge.pack(pady=(16, 6))

        # Big Countdown Label
        self.timer_label = ctk.CTkLabel(
            card,
            text="25:00",
            font=ctk.CTkFont(family=FONT_NAME, size=72, weight="bold"),
            text_color="#10B981"
        )
        self.timer_label.pack(pady=2)

        # Progress indicator bar
        self.progress_bar = ctk.CTkProgressBar(
            card,
            width=360,
            height=6,
            corner_radius=3,
            fg_color=("#E2E8F0", "#0F172A"),
            progress_color="#10B981"
        )
        self.progress_bar.pack(pady=(4, 6))
        self.progress_bar.set(1.0)

        # Session Count Label
        self.session_info_label = ctk.CTkLabel(
            card,
            text="Completed Sessions: 0 • Target: 4 for Long Break",
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            text_color=("#64748B", "#94A3B8")
        )
        self.session_info_label.pack(pady=(0, 12))

        # Primary Control Buttons
        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(pady=6)

        self.btn_primary = ctk.CTkButton(
            btn_box,
            text="▶ Start Focus",
            font=ctk.CTkFont(family=FONT_NAME, size=15, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            text_color="#FFFFFF",
            height=44,
            width=160,
            corner_radius=22,
            command=self._handle_play_pause
        )
        self.btn_primary.pack(side="left", padx=8)

        self.btn_skip = ctk.CTkButton(
            btn_box,
            text="⏭ Skip",
            font=ctk.CTkFont(family=FONT_NAME, size=13, weight="bold"),
            fg_color=("#E2E8F0", "#334155"),
            hover_color=("#CBD5E1", "#475569"),
            text_color=("#0F172A", "#F8FAFC"),
            height=44,
            width=90,
            corner_radius=22,
            command=self._handle_skip
        )
        self.btn_skip.pack(side="left", padx=8)

        self.btn_reset = ctk.CTkButton(
            btn_box,
            text="🔄",
            font=ctk.CTkFont(family=FONT_NAME, size=15),
            fg_color=("#E2E8F0", "#334155"),
            hover_color=("#CBD5E1", "#475569"),
            text_color=("#0F172A", "#F8FAFC"),
            height=44,
            width=48,
            corner_radius=22,
            command=self._handle_reset
        )
        self.btn_reset.pack(side="left", padx=4)

        # Preset Quick Switchers
        presets_frame = ctk.CTkFrame(card, fg_color=("#F8FAFC", "#0F172A"), corner_radius=12)
        presets_frame.pack(fill="x", padx=20, pady=(12, 10))

        p_lbl = ctk.CTkLabel(
            presets_frame,
            text="Quick Mode:",
            font=ctk.CTkFont(family=FONT_NAME, size=12, weight="bold"),
            text_color=("#475569", "#94A3B8")
        )
        p_lbl.pack(side="left", padx=14, pady=8)

        btn_p25 = ctk.CTkButton(
            presets_frame,
            text="25m Pomodoro",
            font=ctk.CTkFont(family=FONT_NAME, size=11, weight="bold"),
            fg_color=("#E2E8F0", "#1E293B"),
            hover_color=("#CBD5E1", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            height=26,
            width=105,
            corner_radius=8,
            command=lambda: self._set_quick_preset(25, 5)
        )
        btn_p25.pack(side="left", padx=4)

        btn_p50 = ctk.CTkButton(
            presets_frame,
            text="50m Deep Work",
            font=ctk.CTkFont(family=FONT_NAME, size=11, weight="bold"),
            fg_color=("#E2E8F0", "#1E293B"),
            hover_color=("#CBD5E1", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            height=26,
            width=105,
            corner_radius=8,
            command=lambda: self._set_quick_preset(50, 10)
        )
        btn_p50.pack(side="left", padx=4)

        btn_break_now = ctk.CTkButton(
            presets_frame,
            text="🌿 Break (5m)",
            font=ctk.CTkFont(family=FONT_NAME, size=11, weight="bold"),
            fg_color="#064E3B",
            hover_color="#047857",
            text_color="#34D399",
            height=26,
            width=90,
            corner_radius=8,
            command=self.engine.start_short_break
        )
        btn_break_now.pack(side="left", padx=4)

        # Health Quick Toggles
        toggles_frame = ctk.CTkFrame(card, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=20, pady=(4, 12))

        self.strict_var = ctk.BooleanVar(value=(self.config.get("break_enforcement_mode") == "strict"))
        chk_strict = ctk.CTkCheckBox(
            toggles_frame,
            text="Strict Full-Screen Break Lock",
            variable=self.strict_var,
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            text_color=("#1E293B", "#CBD5E1"),
            fg_color="#10B981",
            command=self._on_strict_toggle
        )
        chk_strict.pack(side="left", padx=(4, 16))

        self.eye_var = ctk.BooleanVar(value=self.config.get("enable_eye_strain_rule", True))
        chk_eye = ctk.CTkCheckBox(
            toggles_frame,
            text="20-20-20 Eye Strain Care",
            variable=self.eye_var,
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            text_color=("#1E293B", "#CBD5E1"),
            fg_color="#38BDF8",
            command=self._on_eye_toggle
        )
        chk_eye.pack(side="left")

        # Integrated Tasks & Goals Section
        self._build_task_list_section(container)

    def _build_task_list_section(self, parent):
        task_card = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=("#FFFFFF", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        task_card.pack(fill="x", pady=8)

        # Task Header
        t_head = ctk.CTkFrame(task_card, fg_color="transparent")
        t_head.pack(fill="x", padx=16, pady=(12, 6))

        t_title = ctk.CTkLabel(
            t_head,
            text="📋 Focus Tasks & Objectives",
            font=ctk.CTkFont(family=FONT_NAME, size=15, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        t_title.pack(side="left")

        # Add Task Row
        add_box = ctk.CTkFrame(task_card, fg_color="transparent")
        add_box.pack(fill="x", padx=16, pady=(4, 10))

        self.task_entry = ctk.CTkEntry(
            add_box,
            placeholder_text="Enter a task to focus on...",
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            fg_color=("#F1F5F9", "#0F172A"),
            border_color=("#CBD5E1", "#334155"),
            height=32
        )
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.task_entry.bind("<Return>", lambda e: self._on_add_task_clicked())

        self.pomo_target_menu = ctk.CTkOptionMenu(
            add_box,
            values=["1 🍅", "2 🍅", "3 🍅", "4 🍅", "5 🍅"],
            width=75,
            height=32,
            font=ctk.CTkFont(family=FONT_NAME, size=11),
            fg_color=("#E2E8F0", "#334155"),
            button_color=("#CBD5E1", "#475569"),
            text_color=("#0F172A", "#F8FAFC")
        )
        self.pomo_target_menu.set("2 🍅")
        self.pomo_target_menu.pack(side="left", padx=(0, 8))

        btn_add = ctk.CTkButton(
            add_box,
            text="+ Add",
            font=ctk.CTkFont(family=FONT_NAME, size=12, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            width=65,
            height=32,
            corner_radius=8,
            command=self._on_add_task_clicked
        )
        btn_add.pack(side="left")

        # Container for task items
        self.tasks_list_frame = ctk.CTkFrame(task_card, fg_color="transparent")
        self.tasks_list_frame.pack(fill="x", padx=16, pady=(0, 12))

        self._render_tasks_ui()

    def _render_tasks_ui(self):
        for widget in self.tasks_list_frame.winfo_children():
            widget.destroy()

        if not self.tasks.tasks:
            empty_lbl = ctk.CTkLabel(
                self.tasks_list_frame,
                text="No active tasks. Add one above to track your Pomodoro progress!",
                font=ctk.CTkFont(family=FONT_NAME, size=11),
                text_color=("#64748B", "#94A3B8")
            )
            empty_lbl.pack(pady=8)
            return

        for task in self.tasks.tasks:
            t_row = ctk.CTkFrame(
                self.tasks_list_frame,
                fg_color=("#F8FAFC", "#0F172A") if not task["done"] else ("#F1F5F9", "#111827"),
                corner_radius=8
            )
            t_row.pack(fill="x", pady=3)

            is_active = (self.tasks.active_task_id == task["id"])

            # Checkbox
            var = ctk.BooleanVar(value=task["done"])
            chk = ctk.CTkCheckBox(
                t_row,
                text="",
                width=24,
                checkbox_width=18,
                checkbox_height=18,
                variable=var,
                command=lambda t_id=task["id"]: self._toggle_task_done(t_id)
            )
            chk.pack(side="left", padx=(10, 4), pady=6)

            # Title
            title_text = task["title"]
            if is_active and not task["done"]:
                title_text = f"🎯 {title_text}"

            t_lbl = ctk.CTkLabel(
                t_row,
                text=title_text,
                font=ctk.CTkFont(
                    family=FONT_NAME,
                    size=12,
                    weight="bold" if is_active else "normal",
                    overstrike=task["done"]
                ),
                text_color=("#64748B", "#64748B") if task["done"] else (
                    ("#0F172A", "#F8FAFC") if not is_active else "#10B981"
                )
            )
            t_lbl.pack(side="left", padx=4, fill="x", expand=True)

            # Pomodoro Progress Badge
            badge_text = f"🍅 {task['completed_pomodoros']}/{task['target_pomodoros']}"
            p_badge = ctk.CTkLabel(
                t_row,
                text=badge_text,
                font=ctk.CTkFont(family=FONT_NAME, size=11, weight="bold"),
                text_color="#F59E0B" if not task["done"] else "#64748B"
            )
            p_badge.pack(side="left", padx=8)

            # Set as Active Button
            if not task["done"] and not is_active:
                btn_set_act = ctk.CTkButton(
                    t_row,
                    text="Focus",
                    width=48,
                    height=22,
                    font=ctk.CTkFont(family=FONT_NAME, size=10),
                    fg_color=("#E2E8F0", "#334155"),
                    hover_color=("#CBD5E1", "#475569"),
                    text_color=("#0F172A", "#F8FAFC"),
                    command=lambda t_id=task["id"]: self._set_task_active(t_id)
                )
                btn_set_act.pack(side="left", padx=4)

            # Delete button
            btn_del = ctk.CTkButton(
                t_row,
                text="✕",
                width=24,
                height=22,
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                hover_color=("#FEE2E2", "#7F1D1D"),
                text_color=("#EF4444", "#F87171"),
                command=lambda t_id=task["id"]: self._delete_task(t_id)
            )
            btn_del.pack(side="right", padx=6)

    def _on_add_task_clicked(self):
        text = self.task_entry.get().strip()
        if not text:
            return
        target_str = self.pomo_target_menu.get().split()[0]
        try:
            target = int(target_str)
        except Exception:
            target = 2
        self.tasks.add_task(text, target)
        self.task_entry.delete(0, "end")
        self._render_tasks_ui()

    def _toggle_task_done(self, task_id: str):
        self.tasks.toggle_task_done(task_id)
        self._render_tasks_ui()

    def _set_task_active(self, task_id: str):
        self.tasks.set_active_task(task_id)
        self._render_tasks_ui()

    def _delete_task(self, task_id: str):
        self.tasks.delete_task(task_id)
        self._render_tasks_ui()

    def _on_focus_session_finished(self):
        # Auto increment active task completed pomodoro
        self.tasks.record_completed_pomodoro_for_active()
        self.after(0, self._render_tasks_ui)

    # ================= 🎧 SOUNDSCAPES TAB =================
    def _build_soundscapes_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_soundscapes, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # Header card
        header_card = ctk.CTkFrame(
            container,
            fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=14,
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        header_card.pack(fill="x", pady=6)

        h_lbl = ctk.CTkLabel(
            header_card,
            text="🎧 Ambient Focus Soundscapes",
            font=ctk.CTkFont(family=FONT_NAME, size=16, weight="bold"),
            text_color="#10B981"
        )
        h_lbl.pack(anchor="w", padx=16, pady=(12, 4))

        h_sub = ctk.CTkLabel(
            header_card,
            text="Zero-overhead sound loops generated in real-time to drown out distractions and induce flow state.",
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            text_color=("#475569", "#94A3B8"),
            wraplength=560,
            justify="left"
        )
        h_sub.pack(anchor="w", padx=16, pady=(0, 10))

        # Stop Sound Button
        self.btn_stop_sound = ctk.CTkButton(
            header_card,
            text="⏹ Stop Ambient Audio",
            font=ctk.CTkFont(family=FONT_NAME, size=12, weight="bold"),
            fg_color=("#EF4444", "#DC2626"),
            hover_color="#B91C1C",
            text_color="#FFFFFF",
            width=160,
            height=28,
            corner_radius=8,
            command=self._stop_soundscape
        )
        self.btn_stop_sound.pack(anchor="w", padx=16, pady=(0, 14))

        sounds = [
            ("brown_noise", "🌊 Deep Brown Noise", "Warm low-frequency rumble. Scientifically proven for ADHD focus and deep relaxation."),
            ("rain", "🌧️ Soothing Rain", "Gentle rhythmic raindrops masking conversations and busy environments."),
            ("white_noise", "💨 Soft White Noise", "Full-spectrum audio frequencies to balance unpredictable background noises."),
            ("lofi_tick", "🕰️ Relaxing Lofi Ticks", "Gentle wooden clock metronome for calm, time-conscious rhythm.")
        ]

        self.sound_buttons = {}
        for s_id, s_title, s_desc in sounds:
            s_card = ctk.CTkFrame(
                container,
                fg_color=("#FFFFFF", "#1E293B"),
                corner_radius=12,
                border_width=1,
                border_color=("#E2E8F0", "#334155")
            )
            s_card.pack(fill="x", pady=5)

            left_box = ctk.CTkFrame(s_card, fg_color="transparent")
            left_box.pack(side="left", fill="both", expand=True, padx=14, pady=10)

            lbl_t = ctk.CTkLabel(
                left_box,
                text=s_title,
                font=ctk.CTkFont(family=FONT_NAME, size=14, weight="bold"),
                text_color=("#0F172A", "#F8FAFC")
            )
            lbl_t.pack(anchor="w")

            lbl_d = ctk.CTkLabel(
                left_box,
                text=s_desc,
                font=ctk.CTkFont(family=FONT_NAME, size=11),
                text_color=("#475569", "#94A3B8"),
                wraplength=420,
                justify="left"
            )
            lbl_d.pack(anchor="w", pady=(2, 0))

            btn_play = ctk.CTkButton(
                s_card,
                text="▶ Play",
                width=80,
                height=32,
                font=ctk.CTkFont(family=FONT_NAME, size=12, weight="bold"),
                fg_color="#10B981",
                hover_color="#059669",
                corner_radius=16,
                command=lambda name=s_id: self._toggle_soundscape(name)
            )
            btn_play.pack(side="right", padx=16)
            self.sound_buttons[s_id] = btn_play

    def _toggle_soundscape(self, name: str):
        is_playing = self.soundscapes.toggle(name)
        for s_id, btn in self.sound_buttons.items():
            if s_id == name and is_playing:
                btn.configure(text="⏸ Pause", fg_color="#F59E0B")
            else:
                btn.configure(text="▶ Play", fg_color="#10B981")

    def _stop_soundscape(self):
        self.soundscapes.stop()
        for btn in self.sound_buttons.values():
            btn.configure(text="▶ Play", fg_color="#10B981")

    # ================= 🧘 WELLNESS & REST TAB =================
    def _build_wellness_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_wellness, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # Hydration Card
        water_card = ctk.CTkFrame(
            container,
            fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=14,
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        water_card.pack(fill="x", pady=6)

        w_header = ctk.CTkLabel(
            water_card,
            text="💧 Daily Hydration Tracker",
            font=ctk.CTkFont(family=FONT_NAME, size=16, weight="bold"),
            text_color="#0284C7"
        )
        w_header.pack(anchor="w", padx=16, pady=(12, 4))

        self.water_status_label = ctk.CTkLabel(
            water_card,
            text="0 / 8 Glasses Consumed Today",
            font=ctk.CTkFont(family=FONT_NAME, size=13),
            text_color=("#475569", "#94A3B8")
        )
        self.water_status_label.pack(anchor="w", padx=16, pady=(0, 10))

        w_btns = ctk.CTkFrame(water_card, fg_color="transparent")
        w_btns.pack(anchor="w", padx=16, pady=(0, 14))

        btn_add_water = ctk.CTkButton(
            w_btns,
            text="+ Drink 1 Glass",
            font=ctk.CTkFont(family=FONT_NAME, size=12, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            text_color="#FFFFFF",
            corner_radius=10,
            command=self._log_water_cup
        )
        btn_add_water.pack(side="left", padx=(0, 8))

        btn_sub_water = ctk.CTkButton(
            w_btns,
            text="- Remove",
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            fg_color=("#E2E8F0", "#334155"),
            hover_color=("#CBD5E1", "#475569"),
            text_color=("#0F172A", "#F8FAFC"),
            width=80,
            corner_radius=10,
            command=self._remove_water_cup
        )
        btn_sub_water.pack(side="left")

        # Eye Gymnastics Section
        eye_card = ctk.CTkFrame(
            container,
            fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=14,
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        eye_card.pack(fill="x", pady=6)

        e_header = ctk.CTkLabel(
            eye_card,
            text="👁️ Eye Gymnastics & Strain Relief",
            font=ctk.CTkFont(family=FONT_NAME, size=15, weight="bold"),
            text_color="#38BDF8"
        )
        e_header.pack(anchor="w", padx=16, pady=(12, 4))

        eye_exercises = [
            ("• The 20-20-20 Rule:", "Every 20 mins, look at an object 20 feet (6m) away for 20 seconds."),
            ("• Figure-8 Tracing:", "Imagine a giant figure 8 about 10 feet in front of you. Trace it slowly with eyes for 30s."),
            ("• Warm Palm Cupping:", "Rub hands together until warm. Cup palms gently over closed eyes for 30 seconds.")
        ]
        for name, detail in eye_exercises:
            lbl_line = ctk.CTkLabel(
                eye_card,
                text=f"{name} {detail}",
                font=ctk.CTkFont(family=FONT_NAME, size=12),
                text_color=("#475569", "#94A3B8"),
                wraplength=540,
                justify="left"
            )
            lbl_line.pack(anchor="w", padx=16, pady=2)
        eye_card.pack_configure(pady=(6, 10))

        # Stretches List
        stretches_title = ctk.CTkLabel(
            container,
            text="🧘 Quick Ergonomic Desk Stretches",
            font=ctk.CTkFont(family=FONT_NAME, size=16, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        stretches_title.pack(anchor="w", padx=4, pady=(10, 6))

        exercises = [
            ("🧘 Neck & Shoulder Release", "Gently drop chin to chest. Tilt head to right shoulder, then left. Roll shoulders backwards 5 times to release tension."),
            ("🙆 Overhead Spine Extension", "Interlace fingers, rotate palms upward, take a slow deep breath, and reach high toward the ceiling."),
            ("🖐️ Wrist & Finger Mobilizer", "Extend arm straight out, gently pull fingers backward with other hand for 15s. Shake wrists loose."),
            ("🚶 2-Minute Movement Break", "Stand up, walk away from your desk, stretch your hamstrings, and drink fresh water.")
        ]

        for title, desc in exercises:
            s_card = ctk.CTkFrame(
                container,
                fg_color=("#FFFFFF", "#1E293B"),
                corner_radius=12,
                border_width=1,
                border_color=("#E2E8F0", "#334155")
            )
            s_card.pack(fill="x", pady=5)

            lbl_t = ctk.CTkLabel(
                s_card,
                text=title,
                font=ctk.CTkFont(family=FONT_NAME, size=14, weight="bold"),
                text_color="#10B981"
            )
            lbl_t.pack(anchor="w", padx=14, pady=(10, 2))

            lbl_d = ctk.CTkLabel(
                s_card,
                text=desc,
                font=ctk.CTkFont(family=FONT_NAME, size=12),
                text_color=("#475569", "#94A3B8"),
                wraplength=540,
                justify="left"
            )
            lbl_d.pack(anchor="w", padx=14, pady=(0, 10))

    # ================= 📊 STATS & REPORTS TAB =================
    def _build_stats_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_stats, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=4, pady=4)

        # Metric Tiles (Grid 2x2)
        grid = ctk.CTkFrame(container, fg_color="transparent")
        grid.pack(fill="x", pady=6)

        self.tile_focus = self._create_metric_tile(grid, "🎯 Focus Time Today", "0 mins", "#10B981", 0, 0)
        self.tile_sessions = self._create_metric_tile(grid, "🍅 Completed Pomodoros", "0", "#38BDF8", 0, 1)
        self.tile_streak = self._create_metric_tile(grid, "🔥 Focus Streak", "1 Day", "#F59E0B", 1, 0)
        self.tile_breaks = self._create_metric_tile(grid, "🌿 Breaks Honored", "0 / 0", "#A855F7", 1, 1)

        # 7-Day Visual History Chart
        chart_card = ctk.CTkFrame(
            container,
            fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=14,
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        chart_card.pack(fill="x", pady=8)

        ch_head = ctk.CTkFrame(chart_card, fg_color="transparent")
        ch_head.pack(fill="x", padx=16, pady=(12, 4))

        ch_title = ctk.CTkLabel(
            ch_head,
            text="📈 Last 7 Days Activity (Focus Minutes)",
            font=ctk.CTkFont(family=FONT_NAME, size=14, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        ch_title.pack(side="left")

        # Visual Canvas
        self.chart_canvas = ctk.CTkCanvas(
            chart_card,
            height=140,
            bg="#1E293B" if ctk.get_appearance_mode().lower() == "dark" else "#FFFFFF",
            highlightthickness=0
        )
        self.chart_canvas.pack(fill="x", padx=16, pady=(4, 12))

        # Export Report Button
        export_row = ctk.CTkFrame(chart_card, fg_color="transparent")
        export_row.pack(fill="x", padx=16, pady=(0, 12))

        btn_export = ctk.CTkButton(
            export_row,
            text="📥 Export Stats to CSV",
            font=ctk.CTkFont(family=FONT_NAME, size=12, weight="bold"),
            fg_color=("#E2E8F0", "#334155"),
            hover_color=("#CBD5E1", "#475569"),
            text_color=("#0F172A", "#F8FAFC"),
            height=30,
            corner_radius=8,
            command=self._handle_export_csv
        )
        btn_export.pack(side="right")

        self._refresh_stats_ui()

    def _render_chart(self):
        canvas = self.chart_canvas
        canvas.delete("all")

        bg = "#1E293B" if ctk.get_appearance_mode().lower() == "dark" else "#FFFFFF"
        canvas.configure(bg=bg)

        history = self.stats.get_last_7_days_history()
        w = canvas.winfo_width()
        if w < 100:
            w = 540
        h = 130

        max_mins = max([d["focus_minutes"] for d in history] + [60])
        bar_count = len(history)
        slot_w = w / bar_count
        bar_w = slot_w * 0.45

        for i, day in enumerate(history):
            x0 = (i * slot_w) + (slot_w - bar_w) / 2
            x1 = x0 + bar_w

            val = day["focus_minutes"]
            pct = val / max_mins
            bar_h = max(6, pct * (h - 40))
            y1 = h - 22
            y0 = y1 - bar_h

            color = "#10B981" if val > 0 else ("#334155" if bg == "#1E293B" else "#E2E8F0")

            # Draw bar
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

            # Text label value on top
            if val > 0:
                canvas.create_text(
                    (x0 + x1) / 2, y0 - 8,
                    text=f"{val}m",
                    fill="#10B981",
                    font=("Outfit", 9, "bold")
                )

            # Day label below
            canvas.create_text(
                (x0 + x1) / 2, h - 8,
                text=day["label"],
                fill="#94A3B8" if bg == "#1E293B" else "#64748B",
                font=("Outfit", 10)
            )

    def _handle_export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="breakpulse_focus_history.csv"
        )
        if path:
            success = self.stats.export_to_csv(path)
            if success:
                messagebox.showinfo("Export Successful", f"Stats successfully exported to:\n{path}")
            else:
                messagebox.showerror("Export Failed", "Could not export CSV file.")

    def _create_metric_tile(self, parent, title: str, initial_val: str, color: str, row: int, col: int):
        card = ctk.CTkFrame(
            parent,
            fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=14,
            border_width=1,
            border_color=("#E2E8F0", "#334155"),
            width=275,
            height=90
        )
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        card.pack_propagate(False)

        lbl_t = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            text_color=("#475569", "#94A3B8")
        )
        lbl_t.pack(anchor="w", padx=14, pady=(10, 2))

        lbl_v = ctk.CTkLabel(
            card,
            text=initial_val,
            font=ctk.CTkFont(family=FONT_NAME, size=24, weight="bold"),
            text_color=color
        )
        lbl_v.pack(anchor="w", padx=14)

        return lbl_v

    # ================= ⚙️ SETTINGS TAB =================
    def _build_settings_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_settings, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # Appearance Mode Selector Row
        self._create_theme_setting_row(container)

        # Durations Section
        self._create_setting_row(container, "Focus Session Duration (mins):", "focus_duration_mins", [15, 20, 25, 30, 45, 50, 60])
        self._create_setting_row(container, "Short Break Duration (mins):", "short_break_mins", [3, 5, 8, 10])
        self._create_setting_row(container, "Long Break Duration (mins):", "long_break_mins", [10, 15, 20, 30])
        self._create_setting_row(container, "Sessions Before Long Break:", "sessions_before_long_break", [2, 3, 4, 5, 6])
        self._create_setting_row(container, "AFK Idle Timeout (mins):", "idle_threshold_mins", [2, 3, 4, 5, 10])

        # Global Hotkeys Card
        hk_card = ctk.CTkFrame(
            container,
            fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=14,
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        hk_card.pack(fill="x", pady=8)

        hk_title = ctk.CTkLabel(
            hk_card,
            text="⌨️ Global Windows Hotkeys",
            font=ctk.CTkFont(family=FONT_NAME, size=14, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        hk_title.pack(anchor="w", padx=16, pady=(12, 6))

        shortcuts = [
            ("Ctrl + Alt + Space", "Play / Pause Focus Timer"),
            ("Ctrl + Alt + S", "Skip to Next Phase"),
            ("Ctrl + Alt + M", "Toggle Mini HUD Widget"),
            ("Ctrl + Alt + B", "Trigger Instant 1-Min Rest")
        ]
        for key, desc in shortcuts:
            row_k = ctk.CTkFrame(hk_card, fg_color="transparent")
            row_k.pack(fill="x", padx=16, pady=2)
            lbl_k = ctk.CTkLabel(row_k, text=key, font=ctk.CTkFont(family=FONT_NAME, size=12, weight="bold"), text_color="#10B981")
            lbl_k.pack(side="left")
            lbl_d = ctk.CTkLabel(row_k, text=desc, font=ctk.CTkFont(family=FONT_NAME, size=12), text_color=("#64748B", "#94A3B8"))
            lbl_d.pack(side="right")
        hk_card.pack_configure(pady=(6, 12))

        # Toggles Card
        opts_card = ctk.CTkFrame(
            container,
            fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=14,
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        opts_card.pack(fill="x", pady=6)

        self.snd_var = ctk.BooleanVar(value=self.config.get("sound_enabled", True))
        chk_snd = ctk.CTkCheckBox(
            opts_card,
            text="Play soothing audio chimes on transitions",
            variable=self.snd_var,
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            text_color=("#1E293B", "#CBD5E1"),
            command=self._on_sound_toggle
        )
        chk_snd.pack(anchor="w", padx=16, pady=(12, 6))

        self.tray_var = ctk.BooleanVar(value=self.config.get("minimize_to_tray", True))
        chk_tray = ctk.CTkCheckBox(
            opts_card,
            text="Minimize to system tray on window close (X)",
            variable=self.tray_var,
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            text_color=("#1E293B", "#CBD5E1"),
            command=self._on_tray_setting_toggle
        )
        chk_tray.pack(anchor="w", padx=16, pady=(6, 12))

    def _create_theme_setting_row(self, parent):
        row = ctk.CTkFrame(
            parent,
            fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=12,
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        row.pack(fill="x", pady=5)

        lbl = ctk.CTkLabel(
            row,
            text="Appearance Theme:",
            font=ctk.CTkFont(family=FONT_NAME, size=13, weight="bold"),
            text_color=("#0F172A", "#F1F5F9")
        )
        lbl.pack(side="left", padx=16, pady=12)

        cur_mode = self.config.get("appearance_mode", "dark").capitalize()
        self.theme_menu = ctk.CTkOptionMenu(
            row,
            values=["Dark", "Light", "System"],
            width=100,
            height=28,
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            fg_color=("#E2E8F0", "#334155"),
            button_color=("#CBD5E1", "#475569"),
            text_color=("#0F172A", "#F8FAFC"),
            command=self._on_theme_menu_changed
        )
        self.theme_menu.set(cur_mode)
        self.theme_menu.pack(side="right", padx=16)

    def _create_setting_row(self, parent, label_text: str, config_key: str, values: list):
        row = ctk.CTkFrame(
            parent,
            fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=12,
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        row.pack(fill="x", pady=5)

        lbl = ctk.CTkLabel(
            row,
            text=label_text,
            font=ctk.CTkFont(family=FONT_NAME, size=13),
            text_color=("#0F172A", "#F1F5F9")
        )
        lbl.pack(side="left", padx=16, pady=12)

        current_val = str(self.config.get(config_key, values[0]))
        menu = ctk.CTkOptionMenu(
            row,
            values=[str(v) for v in values],
            width=90,
            height=28,
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            fg_color=("#E2E8F0", "#334155"),
            button_color=("#CBD5E1", "#475569"),
            text_color=("#0F172A", "#F8FAFC"),
            command=lambda choice: self._update_config_key(config_key, int(choice))
        )
        menu.set(current_val)
        menu.pack(side="right", padx=16)

    def _update_config_key(self, key: str, value):
        self.config.set(key, value)
        if key == "focus_duration_mins" and self.engine.state == TimerState.IDLE:
            self.engine.reset()

    # ================= THEME SWITCHER LOGIC =================
    def toggle_appearance_mode(self):
        current = ctk.get_appearance_mode().lower()
        new_mode = "light" if current == "dark" else "dark"
        self._set_app_appearance_mode(new_mode)

    def _on_theme_menu_changed(self, choice: str):
        self._set_app_appearance_mode(choice.lower())

    def _set_app_appearance_mode(self, mode_str: str):
        ctk.set_appearance_mode(mode_str)
        self.config.set("appearance_mode", mode_str)

        is_dark = (mode_str != "light")
        self.btn_theme.configure(text="☀️ Light" if is_dark else "🌙 Dark")
        if hasattr(self, "theme_menu"):
            self.theme_menu.set(mode_str.capitalize())
        if hasattr(self, "chart_canvas"):
            self._render_chart()

    # ================= LOGIC & INTERACTION HANDLERS =================
    def _handle_play_pause(self):
        if self.engine.state == TimerState.IDLE:
            self.engine.start_focus()
            self.audio.play_focus_chime()
        else:
            is_paused = self.engine.toggle_pause()
            self._update_play_btn_ui(is_paused)
        return self.engine.is_paused

    def _handle_skip(self):
        self.engine.skip()

    def _handle_reset(self):
        self.engine.reset()

    def _set_quick_preset(self, focus_mins: int, break_mins: int):
        self.config.set("focus_duration_mins", focus_mins)
        self.config.set("short_break_mins", break_mins)
        self.engine.start_focus()
        self.audio.play_focus_chime()

    def _on_strict_toggle(self):
        mode = "strict" if self.strict_var.get() else "gentle"
        self.config.set("break_enforcement_mode", mode)

    def _on_eye_toggle(self):
        self.config.set("enable_eye_strain_rule", self.eye_var.get())

    def _on_sound_toggle(self):
        enabled = self.snd_var.get()
        self.config.set("sound_enabled", enabled)
        self.audio.set_enabled(enabled)

    def _on_tray_setting_toggle(self):
        self.config.set("minimize_to_tray", self.tray_var.get())

    def _log_water_cup(self):
        count = self.stats.log_water(1)
        self.water_status_label.configure(text=f"{count} / 8 Glasses Consumed Today")
        return count

    def _remove_water_cup(self):
        count = self.stats.log_water(-1)
        self.water_status_label.configure(text=f"{count} / 8 Glasses Consumed Today")

    # ================= TIMER CALLBACKS =================
    def _on_timer_tick(self, rem: int, total: int, state: TimerState, sessions: int):
        mins = rem // 60
        secs = rem % 60
        time_str = f"{mins:02d}:{secs:02d}"

        # Update UI thread-safely
        self.after(0, lambda: self._apply_tick_ui(time_str, rem, total, state, sessions))

    def _apply_tick_ui(self, time_str: str, rem: int, total: int, state: TimerState, sessions: int):
        self.timer_label.configure(text=time_str)
        if total > 0:
            pct = max(0.0, min(1.0, rem / total))
            self.progress_bar.set(pct)

        target = self.config.get("sessions_before_long_break", 4)
        self.session_info_label.configure(
            text=f"Completed Sessions: {sessions} • Target: {target} for Long Rest"
        )

        # Update tooltip & mini widget
        self.tray.update_tooltip(f"{state.value}: {time_str}")
        if self.mini_widget and self.mini_widget.winfo_exists():
            self.mini_widget.update_display(time_str, state.value, self.engine.is_paused)

        # Update full-screen overlay if open
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.update_remaining_time(rem)

    def _on_timer_state_change(self, new_state: TimerState, prev_state: TimerState):
        self.after(0, lambda: self._apply_state_change_ui(new_state, prev_state))

    def _apply_state_change_ui(self, new_state: TimerState, prev_state: TimerState):
        badges = {
            TimerState.IDLE: ("● READY TO FOCUS", ("#475569", "#94A3B8"), ("#F1F5F9", "#0F172A"), "#10B981"),
            TimerState.FOCUS: ("● ACTIVE FOCUS SESSION", "#10B981", ("#DCFCE7", "#064E3B"), "#10B981"),
            TimerState.SHORT_BREAK: ("● SHORT BREAK ACTIVE", "#34D399", ("#D1FAE5", "#064E3B"), "#34D399"),
            TimerState.LONG_BREAK: ("● LONG BREAK RECOVERY", "#60A5FA", ("#DBEAFE", "#1E3A8A"), "#38BDF8"),
            TimerState.EYE_BREAK: ("● 20-20-20 EYE STRAIN REST", "#38BDF8", ("#E0F2FE", "#0C4A6E"), "#38BDF8")
        }
        text, txt_col, bg_col, primary_col = badges.get(new_state, ("● READY", ("#475569", "#94A3B8"), ("#F1F5F9", "#0F172A"), "#10B981"))
        self.status_badge.configure(text=text, text_color=txt_col, fg_color=bg_col)
        self.timer_label.configure(text_color=primary_col)
        self.progress_bar.configure(progress_color=primary_col)

        # Play chime
        if new_state in [TimerState.SHORT_BREAK, TimerState.LONG_BREAK]:
            self.audio.play_break_chime()
        elif new_state == TimerState.FOCUS:
            self.audio.play_focus_chime()
        elif new_state == TimerState.EYE_BREAK:
            self.audio.play_eye_chime()

        # Update Play/Pause button
        self._update_play_btn_ui(self.engine.is_paused)

        # Handle Fullscreen Break Overlay
        if new_state in [TimerState.SHORT_BREAK, TimerState.LONG_BREAK, TimerState.EYE_BREAK]:
            if self.config.get("break_enforcement_mode") == "strict":
                self._show_overlay_window(new_state.value)
        else:
            self._close_overlay_window()

        self._refresh_stats_ui()

    def _update_play_btn_ui(self, is_paused: bool):
        if self.engine.state == TimerState.IDLE:
            self.btn_primary.configure(text="▶ Start Focus", fg_color="#10B981")
        elif is_paused:
            self.btn_primary.configure(text="▶ Resume", fg_color="#F59E0B")
        else:
            self.btn_primary.configure(text="⏸ Pause", fg_color="#10B981")

    def _on_idle_pause(self, idle_secs: float):
        self.after(0, lambda: self.status_badge.configure(text="● AUTO-PAUSED (AWAY FROM PC)", text_color="#F59E0B", fg_color=("#FEF3C7", "#451A03")))

    def _show_overlay_window(self, break_type: str):
        if self.overlay_window and self.overlay_window.winfo_exists():
            return
        self.overlay_window = BreakOverlayWindow(
            parent=self,
            break_type=break_type,
            initial_seconds=self.engine.time_remaining,
            on_skip_callback=self.engine.skip,
            on_water_log_callback=self._log_water_cup,
            sound_manager=self.audio
        )

    def _close_overlay_window(self):
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.close_overlay()
            self.overlay_window = None

    def _refresh_stats_ui(self):
        today = self.stats.get_today_stats()
        self.tile_focus.configure(text=f"{today.get('focus_minutes', 0)} mins")
        self.tile_sessions.configure(text=str(today.get("focus_sessions", 0)))
        self.tile_streak.configure(text=f"{today.get('streak', 1)} Day{'s' if today.get('streak', 1) > 1 else ''}")
        self.tile_breaks.configure(text=f"{today.get('breaks_completed', 0)} / {today.get('breaks_completed', 0) + today.get('breaks_skipped', 0)}")
        self.water_status_label.configure(text=f"{today.get('water_glasses', 0)} / 8 Glasses Consumed Today")

        if hasattr(self, "chart_canvas"):
            self.after(100, self._render_chart)

    # ================= MINI WIDGET & TRAY =================
    def toggle_mini_widget(self):
        if self.mini_widget and self.mini_widget.winfo_exists():
            self.mini_widget.destroy()
            self.mini_widget = None
        else:
            self.mini_widget = MiniWidget(
                parent=self,
                on_toggle_play_callback=self._handle_play_pause,
                on_skip_callback=self._handle_skip,
                on_restore_main_callback=self.show_main_window
            )

    def show_main_window(self):
        self.after(0, self._restore_main_threadsafe)

    def _restore_main_threadsafe(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def on_close_requested(self):
        if self.config.get("minimize_to_tray", True):
            self.withdraw()
        else:
            self.quit_app()

    def quit_app(self):
        if self.hotkeys:
            self.hotkeys.stop()
        if self.soundscapes:
            self.soundscapes.stop()
        if self.tray:
            self.tray.stop()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = BreakPulseApp()
    app.mainloop()
