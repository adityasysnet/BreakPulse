import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any

class StatsManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.stats_file = os.path.join(data_dir, "stats.json")
        self.data: Dict[str, Any] = {
            "days": {},
            "streak": 0,
            "last_active_date": ""
        }
        self.load()

    def get_today_key(self) -> str:
        return date.today().isoformat()

    def load(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"[StatsManager] Error loading stats: {e}")
        self._ensure_today_exists()

    def _ensure_today_exists(self):
        today = self.get_today_key()
        if today not in self.data["days"]:
            self.data["days"][today] = {
                "focus_minutes": 0,
                "focus_sessions": 0,
                "breaks_completed": 0,
                "breaks_skipped": 0,
                "water_glasses": 0
            }

    def save(self):
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"[StatsManager] Error saving stats: {e}")

    def add_focus_time(self, seconds: int):
        self._ensure_today_exists()
        today = self.get_today_key()
        mins = seconds // 60
        self.data["days"][today]["focus_minutes"] += mins
        self._update_streak()
        self.save()

    def record_completed_session(self):
        self._ensure_today_exists()
        today = self.get_today_key()
        self.data["days"][today]["focus_sessions"] += 1
        self._update_streak()
        self.save()

    def record_break_completed(self):
        self._ensure_today_exists()
        today = self.get_today_key()
        self.data["days"][today]["breaks_completed"] += 1
        self.save()

    def record_break_skipped(self):
        self._ensure_today_exists()
        today = self.get_today_key()
        self.data["days"][today]["breaks_skipped"] += 1
        self.save()

    def log_water(self, delta: int = 1):
        self._ensure_today_exists()
        today = self.get_today_key()
        current = self.data["days"][today].get("water_glasses", 0)
        self.data["days"][today]["water_glasses"] = max(0, current + delta)
        self.save()
        return self.data["days"][today]["water_glasses"]

    def _update_streak(self):
        today = self.get_today_key()
        last_date = self.data.get("last_active_date", "")

        if not last_date:
            self.data["streak"] = 1
            self.data["last_active_date"] = today
        elif last_date != today:
            last = date.fromisoformat(last_date)
            current = date.today()
            if current - last == timedelta(days=1):
                self.data["streak"] = self.data.get("streak", 0) + 1
            elif current - last > timedelta(days=1):
                self.data["streak"] = 1
            self.data["last_active_date"] = today

    def get_today_stats(self) -> Dict[str, Any]:
        self._ensure_today_exists()
        today = self.get_today_key()
        stats = self.data["days"][today].copy()
        stats["streak"] = self.data.get("streak", 1)
        return stats

    def get_last_7_days_history(self) -> list[dict]:
        """Returns ordered list of the last 7 days with date, day name, and focus minutes."""
        history = []
        today = date.today()
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            key = d.isoformat()
            day_label = d.strftime("%a")  # Mon, Tue, etc.
            day_data = self.data["days"].get(key, {})
            history.append({
                "date": key,
                "label": day_label,
                "focus_minutes": day_data.get("focus_minutes", 0),
                "sessions": day_data.get("focus_sessions", 0)
            })
        return history

    def export_to_csv(self, filepath: str) -> bool:
        """Exports all recorded daily stats to a CSV file."""
        import csv
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Focus Minutes", "Completed Pomodoros", "Breaks Honored", "Breaks Skipped", "Water Glasses"])
                for day_key in sorted(self.data.get("days", {}).keys()):
                    row = self.data["days"][day_key]
                    writer.writerow([
                        day_key,
                        row.get("focus_minutes", 0),
                        row.get("focus_sessions", 0),
                        row.get("breaks_completed", 0),
                        row.get("breaks_skipped", 0),
                        row.get("water_glasses", 0)
                    ])
            return True
        except Exception as e:
            print(f"[StatsManager] CSV export error: {e}")
            return False
