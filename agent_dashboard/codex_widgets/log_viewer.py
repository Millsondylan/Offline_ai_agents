"""Log viewer widget with auto-scroll and filtering."""

from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static, RichLog, Button, Select
from rich.text import Text

from agent_dashboard.core.models import LogEntry, LogLevel


class LogViewer(Widget):
    """Log viewer with filtering and auto-scroll."""

    DEFAULT_CSS = """
    LogViewer {
        height: 100%;
        background: $panel;
        border: tall $primary;
    }

    LogViewer .viewer-header {
        height: 3;
        dock: top;
        background: $boost;
        color: $accent;
        text-style: bold;
        content-align: center middle;
        border-bottom: tall $primary;
    }

    LogViewer .controls-container {
        height: auto;
        dock: top;
        padding: 1;
        background: $surface;
        border-bottom: tall $primary;
    }

    LogViewer Horizontal {
        height: auto;
        align: center middle;
    }

    LogViewer Select {
        width: 20;
        margin-right: 1;
    }

    LogViewer Button {
        margin-right: 1;
    }

    LogViewer RichLog {
        background: $surface;
        color: $text;
        padding: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._logs: list[LogEntry] = []
        self._filter_level = "ALL"
        self._auto_scroll = True

    def compose(self) -> ComposeResult:
        """Compose the log viewer layout."""
        yield Static("EXECUTION LOGS", classes="viewer-header")

        with Vertical(classes="controls-container"):
            with Horizontal():
                yield Select(
                    [("All Levels", "ALL"), ("Info", "INFO"), ("Warning", "WARN"), ("Error", "ERROR")],
                    value="ALL",
                    id="log-filter"
                )
                yield Button("Clear", id="btn-clear-logs", variant="error")
                yield Button("Auto-scroll: ON", id="btn-toggle-scroll", variant="success")

        yield RichLog(highlight=True, markup=True, id="log-display", auto_scroll=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "btn-clear-logs":
            self._clear_logs()
        elif button_id == "btn-toggle-scroll":
            self._toggle_auto_scroll()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle filter selection change."""
        if event.select.id == "log-filter":
            self._filter_level = str(event.value)
            self._refresh_display()

    def update_logs(self, logs: list[LogEntry]) -> None:
        """Update the log display with new logs."""
        new_logs = logs[len(self._logs):]
        self._logs = logs

        if not new_logs:
            return

        log_widget = self.query_one("#log-display", RichLog)

        for log in new_logs:
            if self._should_show_log(log):
                formatted = self._format_log(log)
                log_widget.write(formatted)

    def _should_show_log(self, log: LogEntry) -> bool:
        """Check if log should be shown based on current filter."""
        if self._filter_level == "ALL":
            return True
        return log.level.value == self._filter_level

    def _format_log(self, log: LogEntry) -> Text:
        """Format a log entry with colors and styling."""
        text = Text()

        time_str = log.timestamp.strftime("%H:%M:%S")
        text.append(f"[{time_str}] ", style="dim")
        text.append(f"C{log.cycle:03d} ", style="bold magenta")

        level = log.level
        if level == LogLevel.ERROR:
            text.append("ERROR   ", style="bold red")
        elif level == LogLevel.WARN:
            text.append("WARN    ", style="bold yellow")
        elif level == LogLevel.INFO:
            text.append("INFO    ", style="bold cyan")
        elif level == LogLevel.DEBUG:
            text.append("DEBUG   ", style="dim white")
        else:
            text.append(f"{level.value:8}", style="white")

        text.append(log.message, style="white")

        return text

    def _clear_logs(self) -> None:
        """Clear all logs from display."""
        try:
            log_widget = self.query_one("#log-display", RichLog)
            log_widget.clear()
            self._logs = []
        except Exception:
            pass

    def _toggle_auto_scroll(self) -> None:
        """Toggle auto-scroll on/off."""
        self._auto_scroll = not self._auto_scroll

        try:
            log_widget = self.query_one("#log-display", RichLog)
            log_widget.auto_scroll = self._auto_scroll

            button = self.query_one("#btn-toggle-scroll", Button)
            if self._auto_scroll:
                button.label = "Auto-scroll: ON"
                button.variant = "success"
            else:
                button.label = "Auto-scroll: OFF"
                button.variant = "default"
        except Exception:
            pass

    def _refresh_display(self) -> None:
        """Refresh the entire log display based on current filter."""
        try:
            log_widget = self.query_one("#log-display", RichLog)
            log_widget.clear()

            for log in self._logs:
                if self._should_show_log(log):
                    formatted = self._format_log(log)
                    log_widget.write(formatted)
        except Exception:
            pass
