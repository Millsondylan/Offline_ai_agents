"""Right sidebar showing live metrics and quick stats."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static, ProgressBar
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

from agent_dashboard.core.models import AgentState, TaskStatus


class MetricsSidebar(Widget):
    """Right sidebar with live metrics and stats."""

    DEFAULT_CSS = """
    MetricsSidebar {
        width: 30;
        dock: right;
        background: $panel;
        border-left: tall $primary;
    }

    MetricsSidebar VerticalScroll {
        padding: 1 1;
        height: 100%;
    }

    MetricsSidebar .metrics-title {
        color: $accent;
        text-style: bold;
        padding: 0 0 1 0;
        text-align: center;
    }

    MetricsSidebar .metric-card {
        margin: 0 0 1 0;
        padding: 1;
        background: $surface;
        border: tall $primary;
    }

    MetricsSidebar .metric-label {
        color: $text-muted;
        text-style: bold;
    }

    MetricsSidebar .metric-value {
        color: $text;
        text-style: bold;
        padding: 0 0 0 1;
    }

    MetricsSidebar .metric-value-success {
        color: $success;
        text-style: bold;
    }

    MetricsSidebar .metric-value-warning {
        color: $warning;
        text-style: bold;
    }

    MetricsSidebar .metric-value-error {
        color: $error;
        text-style: bold;
    }

    MetricsSidebar ProgressBar {
        margin: 1 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state: AgentState = AgentState()
        self._tasks_pending = 0
        self._tasks_in_progress = 0
        self._tasks_completed = 0

    def compose(self) -> ComposeResult:
        """Compose the metrics sidebar."""
        with VerticalScroll():
            yield Static("LIVE METRICS", classes="metrics-title")
            yield Static("", id="progress-card", classes="metric-card")
            yield Static("", id="task-stats-card", classes="metric-card")
            yield Static("", id="system-stats-card", classes="metric-card")
            yield Static("", id="current-task-card", classes="metric-card")

    def update_metrics(self, state: AgentState, tasks: list) -> None:
        """Update all metrics displays."""
        self._state = state
        self._calculate_task_stats(tasks)
        self._refresh_all_cards()

    def _calculate_task_stats(self, tasks: list) -> None:
        """Calculate task statistics."""
        self._tasks_pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
        self._tasks_in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        self._tasks_completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)

    def _refresh_all_cards(self) -> None:
        """Refresh all metric cards."""
        try:
            self._update_progress_card()
            self._update_task_stats_card()
            self._update_system_stats_card()
            self._update_current_task_card()
        except Exception:
            pass

    def _update_progress_card(self) -> None:
        """Update progress card with cycle and completion info."""
        card = self.query_one("#progress-card", Static)

        text = Text()
        text.append("Progress\n", style="bold cyan")
        text.append(f"Cycle: ", style="dim")
        text.append(f"{self._state.cycle}\n", style="bold white")
        text.append(f"Progress: ", style="dim")
        text.append(f"{self._state.progress_percent}%", style="bold green")

        card.update(text)

    def _update_task_stats_card(self) -> None:
        """Update task statistics card."""
        card = self.query_one("#task-stats-card", Static)

        text = Text()
        text.append("Task Statistics\n", style="bold cyan")
        text.append(f"Pending: ", style="dim")
        text.append(f"{self._tasks_pending}\n", style="bold yellow")
        text.append(f"In Progress: ", style="dim")
        text.append(f"{self._tasks_in_progress}\n", style="bold blue")
        text.append(f"Completed: ", style="dim")
        text.append(f"{self._tasks_completed}", style="bold green")

        card.update(text)

    def _update_system_stats_card(self) -> None:
        """Update system statistics card."""
        card = self.query_one("#system-stats-card", Static)

        text = Text()
        text.append("System Status\n", style="bold cyan")
        text.append(f"Errors: ", style="dim")
        if self._state.errors > 0:
            text.append(f"{self._state.errors}\n", style="bold red")
        else:
            text.append(f"{self._state.errors}\n", style="bold green")

        text.append(f"Warnings: ", style="dim")
        if self._state.warnings > 0:
            text.append(f"{self._state.warnings}\n", style="bold yellow")
        else:
            text.append(f"{self._state.warnings}\n", style="bold green")

        text.append(f"Mode: ", style="dim")
        text.append(f"{self._state.mode.value}", style="bold white")

        card.update(text)

    def _update_current_task_card(self) -> None:
        """Update current task card."""
        card = self.query_one("#current-task-card", Static)

        text = Text()
        text.append("Current Task\n", style="bold cyan")

        if self._state.current_task:
            task_text = self._state.current_task
            if len(task_text) > 100:
                task_text = task_text[:97] + "..."
            text.append(task_text, style="white")
        else:
            text.append("No active task", style="dim italic")

        card.update(text)
