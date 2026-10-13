import customtkinter as ctk
from typing import Callable, Optional

class MiniWidget(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        on_toggle_play_callback: Callable[[], bool],
        on_skip_callback: Callable[[], None],
        on_restore_main_callback: Callable[[], None]
    ):
        super().__init__(parent)
        self.parent = parent
        self.on_toggle_play = on_toggle_play_callback
        self.on_skip = on_skip_callback
        self.on_restore_main = on_restore_main_callback

        self.title("BreakPulse Mini")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.geometry("260x64+1550+80")  # Positioned comfortably at top-right
        self.configure(fg_color=("#F1F5F9", "#0F172A"))

        # Draggable state
        self._offset_x = 0
        self._offset_y = 0

        self._setup_ui()
        self._bind_drag_events()

    def _setup_ui(self):
        container = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=14,
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        container.pack(fill="both", expand=True, padx=3, pady=3)

        # Mode Icon & Time
        self.label_time = ctk.CTkLabel(
            container,
            text="🎯 25:00",
            font=ctk.CTkFont(family="Outfit", size=16, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        self.label_time.pack(side="left", padx=(14, 10))

        # Controls
        ctrl_box = ctk.CTkFrame(container, fg_color="transparent")
        ctrl_box.pack(side="right", padx=10)

        # Play/Pause
        self.btn_play = ctk.CTkButton(
            ctrl_box,
            text="⏸",
            width=30,
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color="#334155",
            hover_color="#475569",
            command=self._handle_play_pause
        )
        self.btn_play.pack(side="left", padx=2)

        # Skip
        btn_skip = ctk.CTkButton(
            ctrl_box,
            text="⏭",
            width=30,
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color="#334155",
            hover_color="#475569",
            command=self.on_skip
        )
        btn_skip.pack(side="left", padx=2)

        # Maximize / Restore
        btn_restore = ctk.CTkButton(
            ctrl_box,
            text="↗",
            width=30,
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            command=self.on_restore_main
        )
        btn_restore.pack(side="left", padx=2)

    def update_display(self, text_time: str, state_name: str, is_paused: bool):
        icons = {
            "FOCUS": "🎯",
            "SHORT_BREAK": "🌿",
            "LONG_BREAK": "🌴",
            "EYE_BREAK": "👁️",
            "IDLE": "⏸️"
        }
        icon = icons.get(state_name, "⏱️")
        self.label_time.configure(text=f"{icon} {text_time}")
        self.btn_play.configure(text="▶" if is_paused else "⏸")

    def _handle_play_pause(self):
        is_paused = self.on_toggle_play()
        self.btn_play.configure(text="▶" if is_paused else "⏸")

    def _bind_drag_events(self):
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)

    def _on_drag_start(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def _on_drag_motion(self, event):
        x = self.winfo_pointerx() - self._offset_x
        y = self.winfo_pointery() - self._offset_y
        self.geometry(f"+{x}+{y}")
