import customtkinter as ctk
import time
import math
from typing import Callable, Optional

STRETCHES = [
    {
        "title": "🧘 Neck & Shoulder Release",
        "desc": "Drop chin gently toward chest for 5s. Tilt head to right shoulder, then left. Roll shoulders backward 5 times."
    },
    {
        "title": "🙆 Overhead Spine Extension",
        "desc": "Interlace fingers, push palms up toward the ceiling, take a deep breath, and lengthen your spine."
    },
    {
        "title": "🖐️ Wrist & Forearm Flex",
        "desc": "Extend your right arm forward, palm up. Gently pull fingers back with left hand for 10s. Switch hands."
    },
    {
        "title": "👁️ 20-20-20 Eye Horizon Rest",
        "desc": "Look away from screens at an object at least 20 feet (6m) away. Blink deliberately to lubricate your eyes."
    }
]

class BreakOverlayWindow(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        break_type: str,
        initial_seconds: int,
        on_skip_callback: Optional[Callable[[], None]] = None,
        on_water_log_callback: Optional[Callable[[], None]] = None,
        sound_manager=None
    ):
        super().__init__(parent)
        self.parent = parent
        self.break_type = break_type
        self.seconds_remaining = initial_seconds
        self.on_skip_callback = on_skip_callback
        self.on_water_log_callback = on_water_log_callback
        self.sound_manager = sound_manager

        self.title("BreakPulse • Active Rest")
        self.configure(fg_color="#0A0F1D")

        # Fullscreen & topmost
        self.attributes("-topmost", True)
        self.overrideredirect(True)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")

        self.stretch_idx = 0
        self.emergency_countdown = 5
        self.is_emergency_skipping = False

        self._setup_ui(screen_w, screen_h)
        self._start_breathing_animation()

    def _setup_ui(self, screen_w, screen_h):
        # Center container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # 1. Badge & Title
        badge_text = "🌿 SHORT BREAK" if self.break_type == "SHORT_BREAK" else (
            "🌴 LONG REST" if self.break_type == "LONG_BREAK" else "👁️ 20-20-20 EYE REST"
        )
        badge_color = "#064E3B" if self.break_type != "EYE_BREAK" else "#1E3A8A"
        badge_text_color = "#34D399" if self.break_type != "EYE_BREAK" else "#60A5FA"

        badge = ctk.CTkLabel(
            main_frame,
            text=f"  {badge_text}  ",
            font=ctk.CTkFont(family="Outfit", size=14, weight="bold"),
            fg_color=badge_color,
            text_color=badge_text_color,
            corner_radius=16,
            pady=4
        )
        badge.pack(pady=(0, 10))

        title_lbl = ctk.CTkLabel(
            main_frame,
            text="Step Away • Rejuvenate Your Mind & Body",
            font=ctk.CTkFont(family="Outfit", size=26, weight="bold"),
            text_color="#F8FAFC"
        )
        title_lbl.pack(pady=(0, 16))

        # 2. Huge Timer Display
        self.timer_label = ctk.CTkLabel(
            main_frame,
            text=self._format_time(self.seconds_remaining),
            font=ctk.CTkFont(family="Outfit", size=72, weight="bold"),
            text_color="#10B981" if self.break_type != "EYE_BREAK" else "#38BDF8"
        )
        self.timer_label.pack(pady=4)

        # 3. Box Breathing Visualizer (Canvas)
        self.canvas_size = 220
        self.canvas = ctk.CTkCanvas(
            main_frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg="#0A0F1D",
            highlightthickness=0
        )
        self.canvas.pack(pady=12)

        self.breathing_text = ctk.CTkLabel(
            main_frame,
            text="Inhale slowly (4s)...",
            font=ctk.CTkFont(family="Outfit", size=16, weight="bold"),
            text_color="#94A3B8"
        )
        self.breathing_text.pack(pady=(0, 16))

        # 4. Ergonomic Stretch Card
        self.stretch_card = ctk.CTkFrame(
            main_frame,
            fg_color="#1E293B",
            corner_radius=16,
            border_width=1,
            border_color="#334155",
            width=580,
            height=120
        )
        self.stretch_card.pack(pady=8, padx=20)
        self.stretch_card.pack_propagate(False)

        self.stretch_title = ctk.CTkLabel(
            self.stretch_card,
            text=STRETCHES[0]["title"],
            font=ctk.CTkFont(family="Outfit", size=15, weight="bold"),
            text_color="#F1F5F9"
        )
        self.stretch_title.pack(anchor="w", padx=20, pady=(14, 4))

        self.stretch_desc = ctk.CTkLabel(
            self.stretch_card,
            text=STRETCHES[0]["desc"],
            font=ctk.CTkFont(family="Outfit", size=12),
            text_color="#94A3B8",
            wraplength=540,
            justify="left"
        )
        self.stretch_desc.pack(anchor="w", padx=20, pady=(0, 12))

        # 5. Quick Controls: Hydration & Next Stretch
        btn_bar = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_bar.pack(pady=12)

        self.water_btn = ctk.CTkButton(
            btn_bar,
            text="💧 Drink Glass of Water",
            font=ctk.CTkFont(family="Outfit", size=13, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            corner_radius=20,
            command=self._on_water_clicked
        )
        self.water_btn.pack(side="left", padx=8)

        next_stretch_btn = ctk.CTkButton(
            btn_bar,
            text="🔄 Next Stretch Tip",
            font=ctk.CTkFont(family="Outfit", size=13),
            fg_color="#334155",
            hover_color="#475569",
            corner_radius=20,
            command=self._cycle_stretch
        )
        next_stretch_btn.pack(side="left", padx=8)

        # 6. Bottom Emergency Bypass
        self.skip_btn = ctk.CTkButton(
            main_frame,
            text="Emergency Skip Break",
            font=ctk.CTkFont(family="Outfit", size=11),
            fg_color="transparent",
            hover_color="#1E293B",
            text_color="#64748B",
            command=self._handle_skip
        )
        self.skip_btn.pack(pady=(16, 0))

    def update_remaining_time(self, seconds: int):
        self.seconds_remaining = seconds
        self.timer_label.configure(text=self._format_time(seconds))
        if seconds <= 0:
            self.close_overlay()

    def _format_time(self, seconds: int) -> str:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def _cycle_stretch(self):
        self.stretch_idx = (self.stretch_idx + 1) % len(STRETCHES)
        tip = STRETCHES[self.stretch_idx]
        self.stretch_title.configure(text=tip["title"])
        self.stretch_desc.configure(text=tip["desc"])

    def _on_water_clicked(self):
        if self.on_water_log_callback:
            count = self.on_water_log_callback()
            self.water_btn.configure(text=f"💧 Hydrated! ({count} glasses today)")

    def _start_breathing_animation(self):
        self.start_anim_time = time.time()
        self._animate_breathing_loop()

    def _animate_breathing_loop(self):
        if not self.winfo_exists():
            return

        elapsed = (time.time() - self.start_anim_time) % 16.0  # 16-second box cycle
        c = self.canvas_size / 2

        # 4 phases of 4 seconds each:
        # 0..4: Inhale (expanding 35 -> 80)
        # 4..8: Hold (stay at 80)
        # 8..12: Exhale (contracting 80 -> 35)
        # 12..16: Hold (stay at 35)
        if elapsed < 4.0:
            progress = elapsed / 4.0
            r = 35 + (80 - 35) * math.sin(progress * (math.pi / 2))
            phase_text = f"🫁 Inhale slowly... ({int(4 - elapsed)}s)"
            color = "#10B981"
        elif elapsed < 8.0:
            r = 80
            phase_text = f"✨ Hold your breath... ({int(8 - elapsed)}s)"
            color = "#38BDF8"
        elif elapsed < 12.0:
            progress = (elapsed - 8.0) / 4.0
            r = 80 - (80 - 35) * math.sin(progress * (math.pi / 2))
            phase_text = f"🌬️ Exhale gently... ({int(12 - elapsed)}s)"
            color = "#A855F7"
        else:
            r = 35
            phase_text = f"🧘 Rest & hold... ({int(16 - elapsed)}s)"
            color = "#64748B"

        self.canvas.delete("all")
        # Outer soft glow ring
        self.canvas.create_oval(c - r - 8, c - r - 8, c + r + 8, c + r + 8, outline=color, width=2)
        # Inner solid circle
        self.canvas.create_oval(c - r, c - r, c + r, c + r, fill="#1E293B", outline=color, width=3)

        self.breathing_text.configure(text=phase_text, text_color=color)

        self.after(50, self._animate_breathing_loop)

    def _handle_skip(self):
        if not self.is_emergency_skipping:
            self.is_emergency_skipping = True
            self.emergency_countdown = 3
            self._do_emergency_tick()

    def _do_emergency_tick(self):
        if not self.winfo_exists():
            return
        if self.emergency_countdown > 0:
            self.skip_btn.configure(
                text=f"Releasing in {self.emergency_countdown}s... (Click to cancel)",
                text_color="#EF4444"
            )
            self.emergency_countdown -= 1
            self.after(1000, self._do_emergency_tick)
        else:
            if self.on_skip_callback:
                self.on_skip_callback()
            self.close_overlay()

    def close_overlay(self):
        try:
            self.destroy()
        except Exception:
            pass
