"""Project Goal panel with AI-powered task generation and progress tracking."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll, Container
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Button, Input, TextArea, Label, ProgressBar
from rich.text import Text


class ProjectGoalPanel(Widget):
    """Project Goal panel with AI task breakdown and progress tracking."""

    DEFAULT_CSS = """
    ProjectGoalPanel {
        height: 100%;
        background: $panel;
        border: tall $primary;
    }

    ProjectGoalPanel .panel-header {
        height: 3;
        dock: top;
        background: $boost;
        color: $accent;
        text-style: bold;
        content-align: center middle;
        border-bottom: tall $primary;
    }

    ProjectGoalPanel .section {
        margin: 1 2;
        padding: 1;
        background: $surface;
        border: tall $primary;
    }

    ProjectGoalPanel .section-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    ProjectGoalPanel .field-label {
        color: $text;
        text-style: bold;
        margin-bottom: 0;
        margin-top: 1;
    }

    ProjectGoalPanel Label {
        color: $text;
        text-style: bold;
        margin-bottom: 0;
        margin-top: 1;
    }

    ProjectGoalPanel .status-line {
        margin: 1 0;
        color: $text;
    }

    ProjectGoalPanel .success {
        color: $success;
        text-style: bold;
    }

    ProjectGoalPanel .info {
        color: $accent;
        text-style: bold;
    }

    ProjectGoalPanel .warning {
        color: $warning;
        text-style: bold;
    }

    ProjectGoalPanel Input {
        width: 100%;
        margin-bottom: 1;
        background: $boost;
        color: $text;
        border: tall $primary;
    }

    ProjectGoalPanel Input:focus {
        border: tall $accent;
        background: $surface;
    }

    ProjectGoalPanel TextArea {
        width: 100%;
        height: 8;
        margin-bottom: 1;
        background: $boost;
        color: $text;
        border: tall $primary;
    }

    ProjectGoalPanel TextArea:focus {
        border: tall $accent;
        background: $surface;
    }

    ProjectGoalPanel Button {
        margin-right: 1;
        margin-bottom: 1;
    }

    ProjectGoalPanel ProgressBar {
        margin: 1 0;
    }

    ProjectGoalPanel .progress-text {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin: 1 0;
    }

    ProjectGoalPanel .completion-message {
        text-align: center;
        color: $success;
        text-style: bold;
        padding: 2;
        background: $boost;
        margin: 1 0;
    }

    ProjectGoalPanel .help-text {
        color: $text;
        margin: 1 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._project_title = ""
        self._main_objective = ""
        self._completion_threshold = 80
        self._generated_task_count = 0
        self._completed_task_count = 0
        self._is_generating = False

    def compose(self) -> ComposeResult:
        """Compose the project goal panel layout."""
        yield Static("PROJECT GOAL", classes="panel-header")

        with VerticalScroll():
            # Project Goal Section
            with Container(classes="section"):
                yield Static("PROJECT SETUP", classes="section-title")

                yield Label("Project Title:", classes="field-label")
                yield Input(
                    placeholder="e.g., Build REST API, Create web scraper...",
                    id="project-title-input"
                )

                yield Label("Main Objective (describe what you want to accomplish):", classes="field-label")
                yield TextArea(
                    id="project-objective-input",
                    language="markdown"
                )

                yield Label("Completion Threshold (%):", classes="field-label")
                yield Input(
                    placeholder="80",
                    id="completion-threshold-input",
                    type="integer"
                )

                with Horizontal():
                    yield Button("Generate Tasks", id="btn-generate-tasks", variant="success")
                    yield Button("Clear All", id="btn-clear-project", variant="default")

                yield Static("", id="project-status", classes="status-line")

            # Progress Tracking Section
            with Container(classes="section"):
                yield Static("PROJECT PROGRESS", classes="section-title")

                yield ProgressBar(total=100, show_eta=False, id="project-progress-bar")
                yield Static("0% Complete (0/0 tasks)", id="progress-text", classes="progress-text")

                with Horizontal():
                    yield Button("Start Project", id="btn-start-project", variant="primary")
                    yield Button("Refresh Progress", id="btn-refresh-progress", variant="default")

                yield Static("", id="completion-message", classes="completion-message")

            # Info Section
            with Container(classes="section"):
                yield Static("HOW IT WORKS", classes="section-title")
                yield Static(
                    "1. Enter your project title and main objective\n"
                    "2. Click 'Generate Tasks' to use AI to break down your goal\n"
                    "3. Review generated tasks in the Tasks panel\n"
                    "4. Click 'Start Project' to activate tasks and begin\n"
                    "5. Watch progress as the agent completes tasks\n"
                    "6. Project completes when threshold is reached",
                    classes="help-text"
                )

    def on_mount(self) -> None:
        """Initialize panel when mounted."""
        # Set default threshold
        try:
            threshold_input = self.query_one("#completion-threshold-input", Input)
            threshold_input.value = "80"
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "btn-generate-tasks":
            self._handle_generate_tasks()
        elif button_id == "btn-start-project":
            self._handle_start_project()
        elif button_id == "btn-clear-project":
            self._handle_clear_project()
        elif button_id == "btn-refresh-progress":
            self._handle_refresh_progress()

    def _handle_generate_tasks(self) -> None:
        """Handle task generation from project goal."""
        if self._is_generating:
            self.app.notify("Task generation already in progress", severity="warning")
            return

        try:
            # Get inputs
            title_input = self.query_one("#project-title-input", Input)
            objective_input = self.query_one("#project-objective-input", TextArea)
            threshold_input = self.query_one("#completion-threshold-input", Input)

            self._project_title = title_input.value.strip()
            self._main_objective = objective_input.text.strip()

            # Validate inputs
            if not self._project_title:
                self.app.notify("Please enter a project title", severity="warning")
                status_widget = self.query_one("#project-status", Static)
                status_widget.update(Text("Please enter a project title", style="yellow"))
                return

            if not self._main_objective:
                self.app.notify("Please enter a main objective", severity="warning")
                status_widget = self.query_one("#project-status", Static)
                status_widget.update(Text("Please enter a main objective", style="yellow"))
                return

            # Parse threshold
            try:
                threshold_str = threshold_input.value.strip()
                if threshold_str:
                    self._completion_threshold = max(1, min(100, int(threshold_str)))
                else:
                    self._completion_threshold = 80
            except ValueError:
                self._completion_threshold = 80

            # Update status
            self._is_generating = True
            status_widget = self.query_one("#project-status", Static)
            status_widget.update(Text("Generating tasks with AI... Please wait", style="bold yellow"))
            self.app.notify("Generating tasks with AI...", severity="information")

            # Post message to request task generation
            self.post_message(self.GenerateTasksRequested(self._project_title, self._main_objective))

        except Exception as e:
            self._is_generating = False
            self.app.notify(f"Error generating tasks: {str(e)}", severity="error")

    def _handle_start_project(self) -> None:
        """Handle starting the project (activating tasks and agent)."""
        try:
            if self._generated_task_count == 0:
                self.app.notify("Please generate tasks first", severity="warning")
                return

            # Post message to start the project
            self.post_message(self.StartProjectRequested())
            self.app.notify(f"Starting project: {self._project_title}", severity="information")

        except Exception as e:
            self.app.notify(f"Error starting project: {str(e)}", severity="error")

    def _handle_clear_project(self) -> None:
        """Handle clearing the project form."""
        try:
            title_input = self.query_one("#project-title-input", Input)
            objective_input = self.query_one("#project-objective-input", TextArea)
            threshold_input = self.query_one("#completion-threshold-input", Input)
            status_widget = self.query_one("#project-status", Static)

            title_input.value = ""
            objective_input.text = ""
            threshold_input.value = "80"
            status_widget.update("")

            self._project_title = ""
            self._main_objective = ""
            self._completion_threshold = 80

            self.app.notify("Project cleared", severity="information")

        except Exception as e:
            self.app.notify(f"Error clearing project: {str(e)}", severity="error")

    def _handle_refresh_progress(self) -> None:
        """Handle refreshing progress display."""
        self.post_message(self.RefreshProgressRequested())

    def task_generation_complete(self, task_count: int, success: bool) -> None:
        """Called when task generation is complete."""
        self._is_generating = False

        try:
            status_widget = self.query_one("#project-status", Static)

            if success and task_count > 0:
                self._generated_task_count = task_count
                status_widget.update(
                    Text(f"Successfully generated {task_count} tasks! Check Tasks panel", style="bold green")
                )
                self.app.notify(f"Generated {task_count} tasks successfully!", severity="information")
            else:
                status_widget.update(
                    Text("Failed to generate tasks. Please check AI configuration.", style="bold red")
                )
                self.app.notify("Task generation failed", severity="error")

        except Exception:
            pass

    def update_progress(self, total_tasks: int, completed_tasks: int) -> None:
        """Update the progress display."""
        try:
            self._generated_task_count = total_tasks
            self._completed_task_count = completed_tasks

            # Calculate progress percentage
            if total_tasks > 0:
                progress_pct = int((completed_tasks / total_tasks) * 100)
            else:
                progress_pct = 0

            # Update progress bar
            progress_bar = self.query_one("#project-progress-bar", ProgressBar)
            progress_bar.update(progress=progress_pct)

            # Update progress text
            progress_text = self.query_one("#progress-text", Static)
            progress_text.update(
                Text(
                    f"{progress_pct}% Complete ({completed_tasks}/{total_tasks} tasks)",
                    style="bold cyan"
                )
            )

            # Check if project is complete
            completion_msg = self.query_one("#completion-message", Static)
            if total_tasks > 0 and progress_pct >= self._completion_threshold:
                completion_msg.update(
                    Text(
                        f"PROJECT COMPLETE! Reached {progress_pct}% (threshold: {self._completion_threshold}%)",
                        style="bold green"
                    )
                )
            else:
                completion_msg.update("")

        except Exception:
            pass

    class GenerateTasksRequested(Message):
        """Message sent when task generation is requested."""

        def __init__(self, project_title: str, objective: str) -> None:
            super().__init__()
            self.project_title = project_title
            self.objective = objective

    class StartProjectRequested(Message):
        """Message sent when project start is requested."""
        pass

    class RefreshProgressRequested(Message):
        """Message sent when progress refresh is requested."""
        pass
