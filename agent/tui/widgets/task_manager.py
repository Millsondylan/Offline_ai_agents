"""Advanced task management widget with execution tracking."""
from __future__ import annotations

from typing import List, Optional

from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Label, Button, Input, ProgressBar, RichLog


class TaskCard(Static):
    """A card displaying a single task's information."""

    def __init__(self, task_id: str, task_name: str, description: str) -> None:
        super().__init__(classes="task-card", id=f"task-card-{task_id}")
        self.task_id = task_id
        self.task_name = task_name
        self.description = description
        self.status = "pending"
        self.progress = 0.0
        self.verification_passed = 0
        self.verification_failed = 0
        self.verification_total = 0

    def compose(self):
        yield Label(f"[bold]{self.task_name}[/bold]", classes="task-title")
        yield Label(self.description, classes="task-description")
        yield Label(f"Status: {self.status}", id=f"status-{self.task_id}", classes="task-status")
        yield ProgressBar(total=100, id=f"progress-{self.task_id}", classes="task-progress")
        yield Label("Verifications: 0/0 passed", id=f"verifications-{self.task_id}", classes="task-verifications")

        with Horizontal(classes="task-actions"):
            yield Button("View Details", id=f"view-{self.task_id}", classes="task-btn")
            yield Button("Cancel", id=f"cancel-{self.task_id}", classes="task-btn danger", disabled=True)

    def update_status(self, status: str, progress: float = None, passed: int = None, failed: int = None, total: int = None) -> None:
        """Update task status and progress."""
        self.status = status

        # Update status label with color
        status_label = self.query_one(f"#status-{self.task_id}", Label)
        status_colors = {
            "pending": "dim",
            "running": "yellow",
            "verifying": "blue",
            "completed": "green",
            "failed": "red",
            "cancelled": "dim",
        }
        color = status_colors.get(status, "white")
        status_label.update(f"Status: [bold {color}]{status.upper()}[/bold {color}]")

        # Update progress
        if progress is not None:
            self.progress = progress
            progress_bar = self.query_one(f"#progress-{self.task_id}", ProgressBar)
            progress_bar.update(progress=progress)

        # Update verifications
        if passed is not None:
            self.verification_passed = passed
        if failed is not None:
            self.verification_failed = failed
        if total is not None:
            self.verification_total = total

        verif_label = self.query_one(f"#verifications-{self.task_id}", Label)
        if self.verification_total > 0:
            pass_rate = (self.verification_passed / self.verification_total) * 100
            color = "green" if pass_rate >= 80 else "yellow" if pass_rate >= 60 else "red"
            verif_label.update(
                f"Verifications: [bold {color}]{self.verification_passed}/{self.verification_total} passed[/bold {color}] "
                f"({self.verification_failed} failed)"
            )
        else:
            verif_label.update(f"Verifications: {self.verification_passed}/{self.verification_total} passed")

        # Enable/disable cancel button
        cancel_btn = self.query_one(f"#cancel-{self.task_id}", Button)
        cancel_btn.disabled = status not in {"running", "verifying"}


class TaskManager(Static):
    """Advanced task management with execution tracking."""

    def __init__(self) -> None:
        super().__init__(id="task-manager")
        self.title = Label("═══ TASK EXECUTION MANAGER ═══", classes="panel-title")
        self.tasks: dict[str, TaskCard] = {}

    def compose(self):
        yield self.title

        # Task creation section
        yield Label("\nCreate New Task:", classes="section-label")
        with Horizontal(id="create-task-section"):
            yield Input(placeholder="Task name", id="task-name-input")
            yield Button("Create Task", id="create-task-btn", variant="primary")

        with Horizontal(id="task-description-section"):
            yield Input(placeholder="Task description (optional)", id="task-description-input")

        # Configuration section
        yield Label("\nTask Configuration:", classes="section-label")
        with Horizontal(id="task-config"):
            yield Label("Max Duration (s):")
            yield Input(placeholder="3600", id="task-max-duration", value="3600")
            yield Label("Max Verifications:")
            yield Input(placeholder="100", id="task-max-verifications", value="100")

        # Active tasks section
        yield Label("\nActive Tasks:", classes="section-label")
        with VerticalScroll(id="active-tasks-scroll"):
            yield Vertical(id="active-tasks-container")

        # Execution log
        yield Label("\nExecution Log:", classes="section-label")
        with VerticalScroll(id="execution-log-scroll"):
            yield RichLog(id="execution-log", highlight=True, markup=True)

        # Status
        yield Label("", id="task-manager-status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "create-task-btn":
            self._create_task()
        elif button_id and button_id.startswith("view-"):
            task_id = button_id.replace("view-", "")
            self._view_task_details(task_id)
        elif button_id and button_id.startswith("cancel-"):
            task_id = button_id.replace("cancel-", "")
            self._cancel_task(task_id)

    def _create_task(self) -> None:
        """Create a new task."""
        name_input = self.query_one("#task-name-input", Input)
        desc_input = self.query_one("#task-description-input", Input)
        duration_input = self.query_one("#task-max-duration", Input)
        verifications_input = self.query_one("#task-max-verifications", Input)

        task_name = name_input.value.strip()
        description = desc_input.value.strip() or "No description provided"

        if not task_name:
            self._show_status("Please enter a task name", is_error=True)
            return

        try:
            max_duration = int(duration_input.value or "3600")
            max_verifications = int(verifications_input.value or "100")
        except ValueError:
            self._show_status("Invalid duration or verification count", is_error=True)
            return

        # Create task via app
        if hasattr(self.app, "create_execution_task"):
            task_id = self.app.create_execution_task(
                task_name=task_name,
                description=description,
                max_duration=max_duration,
                max_verifications=max_verifications,
            )

            # Add task card to UI
            task_card = TaskCard(task_id, task_name, description)
            self.tasks[task_id] = task_card

            container = self.query_one("#active-tasks-container", Vertical)
            container.mount(task_card)

            # Clear inputs
            name_input.value = ""
            desc_input.value = ""

            self._log(f"✅ Created task: {task_name}")
            self._show_status(f"Task '{task_name}' created successfully")
        else:
            self._show_status("Task creation not available", is_error=True)

    def _view_task_details(self, task_id: str) -> None:
        """View detailed information about a task."""
        if hasattr(self.app, "view_task_execution"):
            self.app.view_task_execution(task_id)
        else:
            self._log(f"📋 Viewing task: {task_id}")

    def _cancel_task(self, task_id: str) -> None:
        """Cancel a running task."""
        if hasattr(self.app, "cancel_execution_task"):
            success = self.app.cancel_execution_task(task_id)
            if success:
                self._log(f"❌ Cancelled task: {task_id}")
                self._show_status(f"Task {task_id} cancelled")

                # Update task card
                if task_id in self.tasks:
                    self.tasks[task_id].update_status("cancelled")
            else:
                self._show_status("Failed to cancel task", is_error=True)

    def update_task_status(self, task_id: str, status: str, progress: float = None,
                          passed: int = None, failed: int = None, total: int = None) -> None:
        """Update a task's status in the UI."""
        if task_id in self.tasks:
            self.tasks[task_id].update_status(status, progress, passed, failed, total)

    def _log(self, message: str) -> None:
        """Add message to execution log."""
        log = self.query_one("#execution-log", RichLog)
        timestamp = self._get_timestamp()
        log.write(f"[dim]{timestamp}[/dim] {message}")

    def _show_status(self, message: str, is_error: bool = False) -> None:
        """Show status message."""
        status = self.query_one("#task-manager-status", Label)
        color = "red" if is_error else "green"
        status.update(f"[bold {color}]{message}[/bold {color}]")

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
