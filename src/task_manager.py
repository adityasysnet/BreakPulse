import json
import os
import uuid
from typing import List, Dict, Any, Optional

class TaskManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.file_path = os.path.join(data_dir, "tasks.json")
        self.tasks: List[Dict[str, Any]] = []
        self.active_task_id: Optional[str] = None
        self.load()

    def load(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])
                    self.active_task_id = data.get("active_task_id", None)
            except Exception as e:
                print(f"[TaskManager] Error loading tasks: {e}")
                self.tasks = []
        else:
            # Default starter sample task
            self.tasks = [
                {
                    "id": str(uuid.uuid4())[:8],
                    "title": "Welcome to BreakPulse: Deep focus session",
                    "target_pomodoros": 2,
                    "completed_pomodoros": 0,
                    "done": False
                }
            ]
            self.active_task_id = self.tasks[0]["id"]
            self.save()

    def save(self):
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({
                    "tasks": self.tasks,
                    "active_task_id": self.active_task_id
                }, f, indent=4)
        except Exception as e:
            print(f"[TaskManager] Error saving tasks: {e}")

    def add_task(self, title: str, target_pomodoros: int = 2) -> Dict[str, Any]:
        task = {
            "id": str(uuid.uuid4())[:8],
            "title": title.strip(),
            "target_pomodoros": max(1, target_pomodoros),
            "completed_pomodoros": 0,
            "done": False
        }
        self.tasks.append(task)
        if not self.active_task_id:
            self.active_task_id = task["id"]
        self.save()
        return task

    def toggle_task_done(self, task_id: str) -> bool:
        for t in self.tasks:
            if t["id"] == task_id:
                t["done"] = not t["done"]
                self.save()
                return t["done"]
        return False

    def delete_task(self, task_id: str):
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        if self.active_task_id == task_id:
            remaining = [t for t in self.tasks if not t["done"]]
            self.active_task_id = remaining[0]["id"] if remaining else None
        self.save()

    def set_active_task(self, task_id: str):
        self.active_task_id = task_id
        self.save()

    def get_active_task(self) -> Optional[Dict[str, Any]]:
        if not self.active_task_id:
            return None
        for t in self.tasks:
            if t["id"] == self.active_task_id:
                return t
        return None

    def record_completed_pomodoro_for_active(self):
        """Called whenever a Pomodoro focus session finishes."""
        active = self.get_active_task()
        if active and not active["done"]:
            active["completed_pomodoros"] += 1
            if active["completed_pomodoros"] >= active["target_pomodoros"]:
                active["done"] = True
            self.save()
