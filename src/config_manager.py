import json
import os
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "focus_duration_mins": 25,
    "short_break_mins": 5,
    "long_break_mins": 15,
    "sessions_before_long_break": 4,
    "enable_eye_strain_rule": True,
    "eye_strain_interval_mins": 20,
    "eye_strain_duration_secs": 20,
    "break_enforcement_mode": "strict",  # "strict" (fullscreen overlay) or "gentle" (banner/alert)
    "emergency_skip_delay_secs": 5,
    "sound_enabled": True,
    "idle_detection_enabled": True,
    "idle_threshold_mins": 4,
    "auto_start_breaks": False,
    "auto_start_focus": False,
    "minimize_to_tray": True,
    "launch_at_startup": False,
    "daily_water_goal": 8,
    "appearance_mode": "dark",  # "dark" or "light"
    "soundscapes_auto_play": False,
    "soundscapes_selected": "brown_noise",
    "global_hotkeys_enabled": True
}

class ConfigManager:
    def __init__(self, config_dir: str = "data"):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "config.json")
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        os.makedirs(self.config_dir, exist_ok=True)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                print(f"[ConfigManager] Error reading config: {e}. Using defaults.")
        else:
            self.save()

    def save(self):
        os.makedirs(self.config_dir, exist_ok=True)
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"[ConfigManager] Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save()

    def update(self, new_settings: Dict[str, Any]):
        self.config.update(new_settings)
        self.save()
