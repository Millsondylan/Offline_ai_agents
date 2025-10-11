"""Task manager panel with persistence helpers."""

from __future__ import annotations

import curses
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..models import Task
from .base import Panel, safe_addstr

KEY_UP = getattr(curses, "KEY_UP", -1)
KEY_DOWN = getattr(curses, "KEY_DOWN", -2)
KEY_NPAGE = getattr(curses, "KEY_NPAGE", -3)
KEY_PPAGE = getattr(curses, "KEY_PPAGE", -4)


class TaskManagerPanel(Panel):
    """Create, edit and activate tasks stored on disk."""

    footer_hint = "N New | E Edit | D Delete | A Activate | ↑/↓ Navigate"
    PAGE_SIZE = 12

    def __init__(self, *, storage_path: Path, interaction) -> None:
        super().__init__(panel_id="tasks", title="Task Manager")
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.interaction = interaction
        self.tasks: List[Task] = []
        self.active_task_id: Optional[int] = None
        self.selected_index = 0
        self.view_offset = 0
        self._next_id = 1
        self._load_tasks()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_tasks(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            raw = json.loads(self.storage_path.read_text())
        except (OSError, json.JSONDecodeError):
            self.tasks = []
            return
        tasks_data = raw if isinstance(raw, list) else raw.get("tasks", [])
        if not isinstance(tasks_data, list):
            tasks_data = []
        self.active_task_id = None
        self.tasks = []
        for entry in tasks_data:
            task = Task(
                id=int(entry["id"]),
                description=entry["description"],
                priority=entry.get("priority", "medium"),
                created_at=datetime.fromisoformat(entry["created_at"])
                if "created_at" in entry
                else datetime.now(),
                status=entry.get("status", "pending"),
            )
            self.tasks.append(task)
            self._next_id = max(self._next_id, task.id + 1)
        self._next_id = max(self._next_id, 1)

    def _save_tasks(self) -> None:
        tasks_payload = [
            {
                **asdict(task),
                "created_at": task.created_at.isoformat(),
            }
            for task in self.tasks
        ]
        try:
            self.storage_path.write_text(json.dumps(tasks_payload, indent=2))
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Task manipulation
    # ------------------------------------------------------------------
    def create_task(self, description: str, *, priority: str = "medium") -> Task:
        task = Task(id=self._next_id, description=description.strip(), priority=priority)
        self._next_id += 1
        was_empty = not self.tasks
        self.tasks.append(task)
        if was_empty:
            self.selected_index = 0
        self._save_tasks()
        return task

    def handle_key(self, key: int) -> bool:
        if key in (ord("n"), ord("N")):
            description = self.interaction.prompt_text("Task description")
            if not description:
                return False
            priority = self.interaction.prompt_text("Priority", default="medium") or "medium"
            self.create_task(description, priority=priority)
            self._save_tasks()
            return True

        if key in (ord("e"), ord("E")) and self.tasks:
            task = self.tasks[self.selected_index]
            new_description = self.interaction.prompt_text(
                "Edit task", default=task.description
            )
            if new_description:
                task.description = new_description.strip()
                self._save_tasks()
                return True
            return False

        if key in (ord("d"), ord("D")) and self.tasks:
            if not self.interaction.confirm("Delete selected task?"):
                return False
            removed = self.tasks.pop(self.selected_index)
            if self.active_task_id == removed.id:
                self.active_task_id = None
            self.selected_index = max(0, self.selected_index - 1)
            self._save_tasks()
            return True

        if key in (ord("a"), ord("A")) and self.tasks:
            task = self.tasks[self.selected_index]
            self.active_task_id = task.id
            self._save_tasks()
            return True

        if key == KEY_UP:
            if self.selected_index > 0:
                self.selected_index -= 1
                if self.selected_index < self.view_offset:
                    self.view_offset = self.selected_index
            return True

        if key == KEY_DOWN:
            if self.selected_index < len(self.tasks) - 1:
                self.selected_index += 1
                bottom = self.view_offset + self.PAGE_SIZE - 1
                if self.selected_index > bottom:
                    self.view_offset = self.selected_index - self.PAGE_SIZE + 1
            return True

        if key == KEY_NPAGE and self.tasks:
            self.view_offset = min(
                self.view_offset + self.PAGE_SIZE, max(0, len(self.tasks) - self.PAGE_SIZE)
            )
            self.selected_index = min(
                max(self.selected_index, self.view_offset), len(self.tasks) - 1
            )
            return True

        if key == KEY_PPAGE and self.tasks:
            self.view_offset = max(0, self.view_offset - self.PAGE_SIZE)
            self.selected_index = max(self.view_offset, self.selected_index)
            return True

        return False

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _visible_tasks(self) -> List[Task]:
        start = self.view_offset
        end = start + self.PAGE_SIZE
        return self.tasks[start:end]

    def render(self, screen, theme) -> None:
        safe_addstr(screen, 0, 0, "Task List", theme.get("highlight"))
        if not self.tasks:
            safe_addstr(screen, 2, 0, "No tasks yet. Press N to create.")
            return

        for idx, task in enumerate(self._visible_tasks()):
            absolute_index = self.view_offset + idx
            prefix = "▶ " if absolute_index == self.selected_index else "  "
            active_marker = " [ACTIVE]" if task.id == self.active_task_id else ""
            line = (
                f"{prefix}{task.description} "
                f"(priority: {task.priority}){active_marker}"
            )
            safe_addstr(screen, 2 + idx, 0, line)

    # ------------------------------------------------------------------
    def capture_state(self) -> dict:
        return {
            "selected_index": self.selected_index,
            "view_offset": self.view_offset,
            "active_task_id": self.active_task_id,
        }

    def restore_state(self, state: dict) -> None:
        self.selected_index = int(state.get("selected_index", 0))
        self.view_offset = int(state.get("view_offset", 0))
        self.active_task_id = state.get("active_task_id")
        self.selected_index = min(self.selected_index, max(0, len(self.tasks) - 1))
