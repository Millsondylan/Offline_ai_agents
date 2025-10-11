"""Task management panel with add, delete, and activate functionality."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Button, Input, DataTable
from rich.text import Text

from agent_dashboard.core.models import Task, TaskStatus


class TaskPanel(Widget):
    """Task management panel showing all tasks with controls."""

    DEFAULT_CSS = """
    TaskPanel {
        height: 100%;
        background: $panel;
        border: tall $primary;
    }

    TaskPanel .panel-header {
        height: 3;
        dock: top;
        background: $boost;
        color: $accent;
        text-style: bold;
        content-align: center middle;
        border-bottom: tall $primary;
    }

    TaskPanel .controls-container {
        height: auto;
        dock: top;
        padding: 1;
        background: $surface;
        border-bottom: tall $primary;
    }

    TaskPanel .controls-row {
        height: auto;
        padding: 0 0 1 0;
    }

    TaskPanel Input {
        width: 1fr;
        margin-right: 1;
    }

    TaskPanel Button {
        min-width: 15;
    }

    TaskPanel DataTable {
        height: 1fr;
        background: $surface;
    }

    TaskPanel .task-status-pending {
        color: $warning;
        text-style: bold;
    }

    TaskPanel .task-status-in-progress {
        color: $accent;
        text-style: bold;
    }

    TaskPanel .task-status-completed {
        color: $success;
        text-style: bold;
    }

    TaskPanel .task-status-failed {
        color: $error;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tasks: list[Task] = []

    def compose(self) -> ComposeResult:
        """Compose the task panel layout."""
        yield Static("TASKS & GOALS", classes="panel-header")

        with Vertical(classes="controls-container"):
            with Horizontal(classes="controls-row"):
                yield Input(placeholder="Enter new task description...", id="task-input")
                yield Button("Add Task", id="btn-add-task", variant="success")

            with Horizontal(classes="controls-row"):
                yield Button("Activate", id="btn-activate-task", variant="primary")
                yield Button("Delete", id="btn-delete-task", variant="error")
                yield Button("Refresh", id="btn-refresh-tasks", variant="default")

        yield DataTable(id="task-table", cursor_type="row", zebra_stripes=True)

    def on_mount(self) -> None:
        """Initialize the task table."""
        table = self.query_one("#task-table", DataTable)
        table.add_columns("ID", "Status", "Description", "Created")
        table.cursor_type = "row"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "btn-add-task":
            self._handle_add_task()
        elif button_id == "btn-activate-task":
            self._handle_activate_task()
        elif button_id == "btn-delete-task":
            self._handle_delete_task()
        elif button_id == "btn-refresh-tasks":
            self.post_message(self.RefreshRequested())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "task-input":
            self._handle_add_task()

    def _handle_add_task(self) -> None:
        """Handle adding a new task."""
        try:
            input_widget = self.query_one("#task-input", Input)
            description = input_widget.value.strip()

            if description:
                self.post_message(self.TaskAdded(description))
                input_widget.value = ""
        except Exception:
            pass

    def _handle_activate_task(self) -> None:
        """Handle activating the selected task."""
        try:
            table = self.query_one("#task-table", DataTable)
            if table.cursor_row is not None and table.cursor_row < len(self._tasks):
                task = self._tasks[table.cursor_row]
                self.post_message(self.TaskActivated(task.id))
        except Exception:
            pass

    def _handle_delete_task(self) -> None:
        """Handle deleting the selected task."""
        try:
            table = self.query_one("#task-table", DataTable)
            if table.cursor_row is not None and table.cursor_row < len(self._tasks):
                task = self._tasks[table.cursor_row]
                self.post_message(self.TaskDeleted(task.id))
        except Exception:
            pass

    def update_tasks(self, tasks: list[Task]) -> None:
        """Update the task table with new task list."""
        try:
            self._tasks = tasks
            self._refresh_table()
        except Exception:
            pass

    def _refresh_table(self) -> None:
        """Refresh the task table display."""
        try:
            table = self.query_one("#task-table", DataTable)
            table.clear()

            for task in self._tasks:
                status_text = self._format_status(task.status)
                description = task.description[:50] + "..." if len(task.description) > 50 else task.description
                created_str = task.created_at.strftime("%Y-%m-%d %H:%M")

                table.add_row(
                    str(task.id),
                    status_text,
                    description,
                    created_str
                )
        except Exception:
            pass

    def _format_status(self, status: TaskStatus) -> Text:
        """Format task status with appropriate color."""
        text = Text()

        if status == TaskStatus.PENDING:
            text.append("PENDING", style="bold yellow")
        elif status == TaskStatus.IN_PROGRESS:
            text.append("IN PROGRESS", style="bold blue")
        elif status == TaskStatus.COMPLETED:
            text.append("COMPLETED", style="bold green")
        elif status == TaskStatus.FAILED:
            text.append("FAILED", style="bold red")
        else:
            text.append(status.value.upper(), style="white")

        return text

    class TaskAdded(Message):
        """Message sent when a task is added."""

        def __init__(self, description: str) -> None:
            super().__init__()
            self.description = description

    class TaskActivated(Message):
        """Message sent when a task is activated."""

        def __init__(self, task_id: int) -> None:
            super().__init__()
            self.task_id = task_id

    class TaskDeleted(Message):
        """Message sent when a task is deleted."""

        def __init__(self, task_id: int) -> None:
            super().__init__()
            self.task_id = task_id

    class RefreshRequested(Message):
        """Message sent when refresh is requested."""
        pass
