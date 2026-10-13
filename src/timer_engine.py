import time
import threading
import sys
from enum import Enum
from typing import Callable, Optional
from src.config_manager import ConfigManager
from src.stats_manager import StatsManager

if sys.platform == "win32":
    import ctypes

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def get_idle_duration_seconds() -> float:
    """Returns number of seconds since last user input on Windows."""
    if sys.platform != "win32":
        return 0.0
    try:
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            return max(0.0, millis / 1000.0)
    except Exception:
        pass
    return 0.0


class TimerState(str, Enum):
    IDLE = "IDLE"
    FOCUS = "FOCUS"
    SHORT_BREAK = "SHORT_BREAK"
    LONG_BREAK = "LONG_BREAK"
    EYE_BREAK = "EYE_BREAK"


class TimerEngine:
    def __init__(self, config: ConfigManager, stats: StatsManager):
        self.config = config
        self.stats = stats

        self.state: TimerState = TimerState.IDLE
        self.is_paused: bool = False

        self.time_remaining: int = 0
        self.current_total_duration: int = 0
        self.completed_focus_sessions: int = 0
        self.eye_strain_counter: int = 0  # elapsed focus seconds since last eye break

        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Callbacks
        self.on_tick: Optional[Callable[[int, int, TimerState, int], None]] = None
        self.on_state_change: Optional[Callable[[TimerState, TimerState], None]] = None
        self.on_idle_pause: Optional[Callable[[float], None]] = None
        self.on_session_completed: Optional[Callable[[], None]] = None

        self._init_timer_for_focus()

    def _init_timer_for_focus(self):
        focus_mins = self.config.get("focus_duration_mins", 25)
        self.current_total_duration = focus_mins * 60
        self.time_remaining = self.current_total_duration

    def start_focus(self):
        with self._lock:
            prev = self.state
            self.state = TimerState.FOCUS
            self.is_paused = False
            self.current_total_duration = self.config.get("focus_duration_mins", 25) * 60
            self.time_remaining = self.current_total_duration
            self._ensure_loop_started()
        if self.on_state_change:
            self.on_state_change(self.state, prev)

    def start_short_break(self):
        with self._lock:
            prev = self.state
            self.state = TimerState.SHORT_BREAK
            self.is_paused = False
            self.current_total_duration = self.config.get("short_break_mins", 5) * 60
            self.time_remaining = self.current_total_duration
            self._ensure_loop_started()
        if self.on_state_change:
            self.on_state_change(self.state, prev)

    def start_long_break(self):
        with self._lock:
            prev = self.state
            self.state = TimerState.LONG_BREAK
            self.is_paused = False
            self.current_total_duration = self.config.get("long_break_mins", 15) * 60
            self.time_remaining = self.current_total_duration
            self._ensure_loop_started()
        if self.on_state_change:
            self.on_state_change(self.state, prev)

    def start_eye_break(self):
        with self._lock:
            prev = self.state
            self.state = TimerState.EYE_BREAK
            self.is_paused = False
            self.current_total_duration = self.config.get("eye_strain_duration_secs", 20)
            self.time_remaining = self.current_total_duration
            self._ensure_loop_started()
        if self.on_state_change:
            self.on_state_change(self.state, prev)

    def toggle_pause(self):
        with self._lock:
            self.is_paused = not self.is_paused
            return self.is_paused

    def pause(self):
        with self._lock:
            self.is_paused = True

    def resume(self):
        with self._lock:
            self.is_paused = False

    def skip(self):
        """Immediately skips the current phase and advances to next phase."""
        with self._lock:
            if self.state in [TimerState.SHORT_BREAK, TimerState.LONG_BREAK, TimerState.EYE_BREAK]:
                self.stats.record_break_skipped()
            self._handle_phase_completion(skipped=True)

    def reset(self):
        with self._lock:
            prev = self.state
            self.state = TimerState.IDLE
            self.is_paused = False
            self._init_timer_for_focus()
        if self.on_state_change:
            self.on_state_change(self.state, prev)

    def _ensure_loop_started(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def _run_loop(self):
        while self._running:
            time.sleep(1)
            with self._lock:
                if self.state == TimerState.IDLE or self.is_paused:
                    continue

                # Idle detection during focus
                if self.state == TimerState.FOCUS and self.config.get("idle_detection_enabled", True):
                    idle_secs = get_idle_duration_seconds()
                    threshold_secs = self.config.get("idle_threshold_mins", 4) * 60
                    if idle_secs >= threshold_secs:
                        self.is_paused = True
                        if self.on_idle_pause:
                            self.on_idle_pause(idle_secs)
                        continue

                # Normal decrement
                self.time_remaining -= 1

                # Track stats for focus mode
                if self.state == TimerState.FOCUS:
                    self.stats.add_focus_time(1)
                    if self.config.get("enable_eye_strain_rule", True):
                        self.eye_strain_counter += 1
                        eye_interval = self.config.get("eye_strain_interval_mins", 20) * 60
                        if self.eye_strain_counter >= eye_interval:
                            self.eye_strain_counter = 0
                            # Trigger eye break
                            threading.Thread(target=self.start_eye_break, daemon=True).start()
                            continue

                rem = self.time_remaining
                total = self.current_total_duration
                cur_state = self.state
                sessions = self.completed_focus_sessions

            # Outside lock tick
            if self.on_tick:
                self.on_tick(rem, total, cur_state, sessions)

            if rem <= 0:
                with self._lock:
                    self._handle_phase_completion(skipped=False)

    def _handle_phase_completion(self, skipped: bool = False):
        prev = self.state

        if prev == TimerState.FOCUS:
            if not skipped:
                self.stats.record_completed_session()
                self.completed_focus_sessions += 1
                if self.on_session_completed:
                    self.on_session_completed()

            # Decide short vs long break
            sessions_target = self.config.get("sessions_before_long_break", 4)
            if self.completed_focus_sessions > 0 and self.completed_focus_sessions % sessions_target == 0:
                next_state = TimerState.LONG_BREAK
                dur = self.config.get("long_break_mins", 15) * 60
            else:
                next_state = TimerState.SHORT_BREAK
                dur = self.config.get("short_break_mins", 5) * 60

            self.state = next_state
            self.current_total_duration = dur
            self.time_remaining = dur
            self.is_paused = not self.config.get("auto_start_breaks", False)

        elif prev in [TimerState.SHORT_BREAK, TimerState.LONG_BREAK]:
            if not skipped:
                self.stats.record_break_completed()

            self.state = TimerState.FOCUS
            dur = self.config.get("focus_duration_mins", 25) * 60
            self.current_total_duration = dur
            self.time_remaining = dur
            self.is_paused = not self.config.get("auto_start_focus", False)

        elif prev == TimerState.EYE_BREAK:
            if not skipped:
                self.stats.record_break_completed()

            # Return directly to focus session without incrementing focus session count
            self.state = TimerState.FOCUS
            # Restore remaining focus time or keep going
            self.is_paused = False

        if self.on_state_change:
            self.on_state_change(self.state, prev)
