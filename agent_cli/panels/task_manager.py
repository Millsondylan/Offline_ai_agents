"""Task Manager panel implementation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Protocol

from agent_cli.models import Task
from agent_cli.panels.base import Panel
from agent_cli.theme import ThemeManager

KEY_UP = 259
KEY_DOWN = 258
KEY_PPAGE = 339
KEY_NPAGE = 338

_VALID_PRIORITIES = {"low", "medium", "high"}


class Interaction(Protocol):
    def prompt_text(self, prompt: str, *, default: str = "", title: str = "") -> Optional[str]:
        ...

    def confirm(self, message: str) -> bool:
        ...

    def notify(self, message: str) -> None:
        ...


class TaskManagerPanel(Panel):
    """Manage agent tasks with keyboard-driven CRUD controls."""

    def __init__(
        self,
        *,
        storage_path: Optional[Path] = None,
        interaction: Optional[Interaction] = None,
        page_size: int = 12,
    ) -> None:
        super().__init__(panel_id="tasks", title="Task Manager")
        self.interaction = interaction
        self.page_size = max(5, page_size)
        self.storage_path = storage_path or self._default_storage_path()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.tasks: List[Task] = []
        self.selected_index = 0
        self.view_offset = 0
        self.active_task_id: Optional[int] = None
        self._next_id = 1
        self._last_message: Optional[str] = None

        self._load_tasks()

    # ------------------------------------------------------------------
    def create_task(self, description: str, priority: str = "medium") -> Task:
        if not description.strip():
            raise ValueError("Task description cannot be empty")
        normalized_priority = self._normalize_priority(priority)
        now = datetime.now()
        task = Task(
            id=self._next_id,
            description=description.strip(),
            status="pending",
            priority=normalized_priority,
            created_at=now,
            updated_at=now,
        )
        self.tasks.append(task)
        self._next_id += 1
        self.selected_index = len(self.tasks) - 1
        self._ensure_selection_visible()
        self._persist()
        self.mark_dirty()
        return task

    def handle_key(self, key: int) -> bool:
        if key in (KEY_UP, ):
            return self._move_selection(-1)
        if key in (KEY_DOWN, ):
            return self._move_selection(1)
        if key == KEY_PPAGE:
            return self._page(-1)
        if key == KEY_NPAGE:
            return self._page(1)

        if key in (ord("N"), ord("n")):
            return self._handle_new_task()
        if key in (ord("E"), ord("e")):
            return self._handle_edit_task()
        if key in (ord("D"), ord("d")):
            return self._handle_delete_task()
        if key in (ord("A"), ord("a")):
            return self._handle_activate_task()
        return False

    # ------------------------------------------------------------------
    def render(self, screen, theme: ThemeManager) -> None:  # type: ignore[override]
        screen.addstr(3, 2, "ID  Status        Priority  Description")
        screen.addstr(4, 2, "──  ───────────  ────────  ─────────────────────────────────────")

        if not self.tasks:
            screen.addstr(6, 2, "No tasks yet. Press N to create.")
        else:
            for idx, task in enumerate(self._visible_tasks()):
                global_index = self.view_offset + idx
                indicator = "→" if global_index == self.selected_index else " "
                status_label = "[ACTIVE]" if task.id == self.active_task_id else f"[{task.status.upper():8}]"
                line = f"{indicator} {task.id:<2} {status_label:10}  {task.priority.title():<8}  {task.description}"
                screen.addstr(5 + idx, 2, line[: 76])

        controls = "[N]ew [E]dit [D]elete [A]ctivate [Enter] Details"
        screen.addstr(20, 2, controls[: 76])
        if self._last_message:
            screen.addstr(21, 2, f"{self._last_message}"[: 76])

    def footer(self) -> str:
        return "N: New | E: Edit | D: Delete | A: Activate | PgUp/PgDn paginate"

    def capture_state(self) -> Dict[str, int | Optional[int]]:
        return {
            "selected_index": self.selected_index,
            "view_offset": self.view_offset,
            "active_task_id": self.active_task_id,
        }

    def restore_state(self, state: Dict[str, int | Optional[int]]) -> None:
        self.selected_index = int(state.get("selected_index", 0))
        self.view_offset = int(state.get("view_offset", 0))
        active = state.get("active_task_id")
        self.active_task_id = int(active) if isinstance(active, (int, float)) else None
        self._ensure_selection_bounds()
        self.mark_dirty()

    # ------------------------------------------------------------------
    def _handle_new_task(self) -> bool:
        if self.interaction is None:
            return False
        description = self.interaction.prompt_text("Task description", title="New Task")
        if not description or not description.strip():
            self._set_message("Task creation cancelled (empty description)")
            return False
        priority = self.interaction.prompt_text(
            "Priority (low/medium/high)", default="medium", title="New Task"
        )
        priority_value = self._normalize_priority(priority or "medium")
        task = self.create_task(description.strip(), priority=priority_value)
        self._set_message(f"Created task #{task.id}")
        return True

    def _handle_edit_task(self) -> bool:
        if not self.tasks or self.interaction is None:
            return False
        task = self.tasks[self.selected_index]
        new_description = self.interaction.prompt_text(
            "Edit description", default=task.description, title="Edit Task"
        )
        if new_description is None:
            self._set_message("Edit cancelled")
            return False
        new_desc = new_description.strip()
        if not new_desc:
            self._set_message("Description cannot be empty")
            return False
        task.description = new_desc
        task.updated_at = datetime.now()
        self._persist()
        self.mark_dirty()
        self._set_message(f"Updated task #{task.id}")
        return True

    def _handle_delete_task(self) -> bool:
        if not self.tasks or self.interaction is None:
            return False
        task = self.tasks[self.selected_index]
        if not self.interaction.confirm(f"Delete task #{task.id}? This cannot be undone."):
            self._set_message("Deletion cancelled")
            return False
        self.tasks.pop(self.selected_index)
        if task.id == self.active_task_id:
            self.active_task_id = None
        self._ensure_selection_bounds()
        self._persist()
        self.mark_dirty()
        self._set_message(f"Deleted task #{task.id}")
        return True

    def _handle_activate_task(self) -> bool:
        if not self.tasks:
            return False
        task = self.tasks[self.selected_index]
        self.active_task_id = task.id
        task.status = "in_progress"
        task.updated_at = datetime.now()
        self._persist()
        self.mark_dirty()
        self._set_message(f"Activated task #{task.id}")
        return True

    def _move_selection(self, delta: int) -> bool:
        if not self.tasks:
            return False
        new_index = self.selected_index + delta
        new_index = max(0, min(len(self.tasks) - 1, new_index))
        if new_index == self.selected_index:
            return False
        self.selected_index = new_index
        self._ensure_selection_visible()
        self.mark_dirty()
        return True

    def _page(self, delta: int) -> bool:
        if not self.tasks:
            return False
        new_offset = self.view_offset + delta * self.page_size
        new_offset = max(0, min(max(0, len(self.tasks) - self.page_size), new_offset))
        if new_offset == self.view_offset:
            return False
        self.view_offset = new_offset
        self._ensure_selection_visible(force=True)
        self.mark_dirty()
        return True

    def _ensure_selection_visible(self, force: bool = False) -> None:
        if not self.tasks:
            self.selected_index = 0
            self.view_offset = 0
            return
        if force:
            if self.selected_index < self.view_offset:
                self.view_offset = self.selected_index
            elif self.selected_index >= self.view_offset + self.page_size:
                self.view_offset = max(0, self.selected_index - self.page_size + 1)
            return
        if self.selected_index < self.view_offset:
            self.view_offset = self.selected_index
        elif self.selected_index >= self.view_offset + self.page_size:
            self.view_offset = self.selected_index - self.page_size + 1

    def _ensure_selection_bounds(self) -> None:
        if not self.tasks:
            self.selected_index = 0
            self.view_offset = 0
            return
        self.selected_index = min(self.selected_index, len(self.tasks) - 1)
        self._ensure_selection_visible(force=True)

    def _visible_tasks(self) -> List[Task]:
        end = self.view_offset + self.page_size
        return self.tasks[self.view_offset : end]

    def _set_message(self, message: str) -> None:
        self._last_message = message

    def _persist(self) -> None:
        payload = []
        for task in self.tasks:
            payload.append(
                {
                    "id": task.id,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
            )
        self.storage_path.write_text(json.dumps(payload, indent=2))

    def _load_tasks(self) -> None:
        if not self.storage_path.exists():
            self.storage_path.write_text("[]")
            return
        try:
            data = json.loads(self.storage_path.read_text())
        except json.JSONDecodeError:
            data = []
        for entry in data:
            task = Task(
                id=int(entry.get("id", self._next_id)),
                description=entry.get("description", ""),
                status=entry.get("status", "pending"),
                priority=self._normalize_priority(entry.get("priority", "medium")),
                created_at=self._parse_datetime(entry.get("created_at")),
                updated_at=self._parse_datetime(entry.get("updated_at")),
            )
            self.tasks.append(task)
            self._next_id = max(self._next_id, task.id + 1)
        if self.tasks:
            self.active_task_id = next((task.id for task in self.tasks if task.status == "in_progress"), None)
        self._ensure_selection_bounds()

    def _normalize_priority(self, priority: str) -> str:
        if priority is None:
            return "medium"
        normalized = priority.strip().lower()
        if normalized not in _VALID_PRIORITIES:
            return "medium"
        return normalized

    def _default_storage_path(self) -> Path:
        return Path.home() / ".agent_cli" / "tasks.json"

    def _parse_datetime(self, value: Optional[str]) -> datetime:
        if not value:
            return datetime.now()
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.now()


__all__ = [
    "TaskManagerPanel",
    "KEY_UP",
    "KEY_DOWN",
    "KEY_PPAGE",
    "KEY_NPAGE",
]
