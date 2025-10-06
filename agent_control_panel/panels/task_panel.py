"""Task management panel."""

import curses
from datetime import datetime
from typing import List

from agent_control_panel.core.models import Task, TaskStatus, TaskPriority
from agent_control_panel.panels.base_panel import BasePanel
from agent_control_panel.utils.keyboard import Key, KeyType, MappedKey


class TaskPanel(BasePanel):
    """Panel for managing tasks."""

    def __init__(self, window, state_manager=None):
        super().__init__("Tasks", window, state_manager)
        self.tasks: List[Task] = []
        self.selected_index = 0
        self.next_id = 1

    def handle_key(self, key: MappedKey) -> bool:
        """Handle keyboard input."""
        if key.type == KeyType.ARROW:
            if key == Key.UP and self.selected_index > 0:
                self.selected_index -= 1
                return True
            elif key == Key.DOWN and self.selected_index < len(self.tasks) - 1:
                self.selected_index += 1
                return True
        elif key.type == KeyType.CHAR:
            if key.value == 'n' or key.value == 'N':
                self._create_task()
                return True
            elif key.value == 'd' or key.value == 'D':
                self._delete_task()
                return True

        return False

    def _create_task(self):
        """Create a new task."""
        # In real implementation, would show input dialog
        now = datetime.now()
        task = Task(
            id=self.next_id,
            description=f"New Task {self.next_id}",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            created_at=now,
            updated_at=now,
        )
        self.tasks.append(task)
        self.next_id += 1

    def _delete_task(self):
        """Delete selected task."""
        if 0 <= self.selected_index < len(self.tasks):
            del self.tasks[self.selected_index]
            if self.selected_index >= len(self.tasks):
                self.selected_index = max(0, len(self.tasks) - 1)

    def render(self) -> None:
        """Render the task list."""
        self._render_title("Task Manager")

        if not self.tasks:
            self._safe_addstr(2, 2, "No tasks yet. Press N to create.")
            return

        y = 2
        for i, task in enumerate(self.tasks):
            prefix = "→ " if i == self.selected_index else "  "
            status_icon = {
                TaskStatus.PENDING: "○",
                TaskStatus.IN_PROGRESS: "◐",
                TaskStatus.COMPLETED: "●",
                TaskStatus.FAILED: "✗",
            }[task.status]

            text = f"{prefix}{status_icon} {task.description}"
            attr = curses.A_REVERSE if i == self.selected_index else curses.A_NORMAL
            self._safe_addstr(y + i, 2, text, attr)
