from __future__ import annotations

from typing import List

from textual.containers import Vertical, VerticalScroll
from textual.widgets import Input, Label, Static

from ..navigation import NavEntry, NavigationItem
from ..state_watcher import TaskState

_STATUS_ICON = {
    "running": "▶",
    "in_progress": "▶",
    "active": "▶",
    "paused": "⏸",
    "pending": "□",
    "queued": "□",
    "waiting": "□",
    "complete": "✓",
    "completed": "✓",
    "done": "✓",
    "failed": "✗",
}


class TaskButton(NavigationItem):
    def __init__(self, task_id: str, label: str, status: str, index: int) -> None:
        self.task_id = task_id
        self.status = status
        super().__init__(label, "Toggle task", id=f"task-{index}")

    def update_status(self, label: str, status: str) -> None:
        self.status = status
        self.set_display(label)

    def handle_enter(self) -> None:  # type: ignore[override]
        getattr(self.app, "toggle_task", lambda _task_id: None)(self.task_id)


class NewTaskButton(NavigationItem):
    def __init__(self, queue: "TaskQueue") -> None:
        super().__init__("[+ New Task]", "Add new task", id="task-new")
        self.queue = queue

    def handle_enter(self) -> None:  # type: ignore[override]
        self.queue.prompt_new_task()


class TaskNameInput(Input):
    BINDINGS = []

    def __init__(self, queue: "TaskQueue") -> None:
        super().__init__(placeholder="Task name", id="task-name-input")
        self.queue = queue

    async def on_mount(self) -> None:  # type: ignore[override]
        self.focus()

    async def on_key(self, event) -> None:  # type: ignore[override]
        if event.key == "escape":
            event.stop()
            self.queue.cancel_new_task()

    async def on_submitted(self, event: Input.Submitted) -> None:  # type: ignore[override]
        name = (event.value or "").strip()
        self.queue.submit_new_task(name)


class TaskQueue(Static):
    def __init__(self) -> None:
        super().__init__(id="task-queue")
        self.title = Label("Task Queue", id="tasks-title")
        self.tasks_scroll = VerticalScroll(id="tasks-scroll")
        self.tasks_container = Vertical(id="tasks-container")
        self.new_task_button = NewTaskButton(self)
        self.new_task_input: TaskNameInput | None = None
        self._nav_entries: List[NavEntry] = []
        self._empty_label: Label | None = None

    def compose(self):
        # Prevent scroll container from stealing focus
        self.tasks_scroll.can_focus = False

        with Vertical(id="task-panel"):
            yield self.title
            with self.tasks_scroll:
                yield self.tasks_container
            yield self.new_task_button

    def update_tasks(self, tasks: List[TaskState]) -> None:
        existing = list(self.tasks_container.children)
        for child in existing:
            if self.new_task_input is not None and child is self.new_task_input:
                continue
            child.remove()

        self._nav_entries = []
        if not tasks:
            if self._empty_label is None:
                self._empty_label = Label("No tasks queued", classes="dim")
            if self._empty_label not in self.tasks_container.children:
                self.tasks_container.mount(self._empty_label)
            self.refresh()
            return
        if self._empty_label is not None and self._empty_label in self.tasks_container.children:
            self._empty_label.remove()
        for index, task in enumerate(tasks):
            icon = _STATUS_ICON.get(task.status.lower(), "□")
            label = f"{icon} {task.title}"
            button = TaskButton(task.identifier, label, task.status, index)
            self.tasks_container.mount(button)
            self._nav_entries.append(NavEntry(widget_id=button.id or f"task-{index}", action=button.enter_action))
        self.refresh()

    def nav_entries(self) -> List[NavEntry]:
        entries = list(self._nav_entries)
        entries.append(NavEntry(widget_id=self.new_task_button.id or "task-new", action=self.new_task_button.enter_action))
        return entries

    def prompt_new_task(self) -> None:
        if self.new_task_input is not None:
            return
        self.new_task_input = TaskNameInput(self)
        self.tasks_container.mount(self.new_task_input)
        self.new_task_input.focus()

    def cancel_new_task(self) -> None:
        if self.new_task_input is None:
            return
        self.new_task_input.remove()
        self.new_task_input = None
        self.new_task_button.focus()

    def submit_new_task(self, name: str) -> None:
        if not name:
            self.cancel_new_task()
            return
        getattr(self.app, "create_task", lambda _name: None)(name)
        self.cancel_new_task()
