"""Top status bar widget showing model, session, cycle, status, and elapsed time."""

from datetime import timedelta
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Static
from rich.text import Text

from agent_dashboard.core.models import AgentState, AgentStatus


class StatusHeader(Widget):
    """Top status bar with key metrics."""

    DEFAULT_CSS = """
    StatusHeader {
        height: 3;
        dock: top;
        background: $panel;
        border-bottom: tall $primary;
    }

    StatusHeader Horizontal {
        height: 100%;
        align: center middle;
    }

    StatusHeader .status-item {
        padding: 0 2;
        height: 100%;
        content-align: center middle;
    }

    StatusHeader .status-label {
        color: $text-muted;
        text-style: bold;
    }

    StatusHeader .status-value {
        color: $text;
        text-style: bold;
    }

    StatusHeader .status-running {
        color: $success;
        text-style: bold;
    }

    StatusHeader .status-stopped {
        color: $error;
        text-style: bold;
    }

    StatusHeader .status-idle {
        color: $warning;
        text-style: bold;
    }

    StatusHeader .status-paused {
        color: $accent;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state: AgentState = AgentState()

    def compose(self) -> ComposeResult:
        """Compose the status header layout."""
        with Horizontal():
            yield Static("", id="model-display", classes="status-item")
            yield Static("", id="session-display", classes="status-item")
            yield Static("", id="cycle-display", classes="status-item")
            yield Static("", id="status-display", classes="status-item")
            yield Static("", id="time-display", classes="status-item")

    def update_state(self, state: AgentState) -> None:
        """Update the status header with new state."""
        self._state = state
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh all status display elements."""
        try:
            self._update_model()
            self._update_session()
            self._update_cycle()
            self._update_status()
            self._update_time()
        except Exception:
            pass

    def _update_model(self) -> None:
        """Update model display."""
        model_widget = self.query_one("#model-display", Static)
        text = Text()
        text.append("MODEL: ", style="dim")
        text.append(self._state.model or "N/A", style="bold cyan")
        model_widget.update(text)

    def _update_session(self) -> None:
        """Update session ID display."""
        session_widget = self.query_one("#session-display", Static)
        text = Text()
        text.append("SESSION: ", style="dim")
        text.append(self._state.session_id, style="bold magenta")
        session_widget.update(text)

    def _update_cycle(self) -> None:
        """Update cycle counter display."""
        cycle_widget = self.query_one("#cycle-display", Static)
        text = Text()
        text.append("CYCLE: ", style="dim")
        text.append(f"{self._state.cycle}", style="bold blue")
        cycle_widget.update(text)

    def _update_status(self) -> None:
        """Update status display with colored indicators."""
        status_widget = self.query_one("#status-display", Static)
        text = Text()
        text.append("STATUS: ", style="dim")

        status = self._state.status
        if status == AgentStatus.RUNNING:
            text.append("RUNNING", style="bold green")
        elif status == AgentStatus.STOPPED:
            text.append("STOPPED", style="bold red")
        elif status == AgentStatus.PAUSED:
            text.append("PAUSED", style="bold yellow")
        elif status == AgentStatus.ERROR:
            text.append("ERROR", style="bold red blink")
        else:
            text.append("IDLE", style="bold yellow")

        status_widget.update(text)

    def _update_time(self) -> None:
        """Update elapsed time display."""
        time_widget = self.query_one("#time-display", Static)
        text = Text()
        text.append("TIME: ", style="dim")

        elapsed = self._state.elapsed_seconds
        if elapsed > 0:
            td = timedelta(seconds=elapsed)
            hours, remainder = divmod(int(td.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            text.append(time_str, style="bold white")
        else:
            text.append("00:00:00", style="dim")

        time_widget.update(text)
