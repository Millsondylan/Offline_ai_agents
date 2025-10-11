"""Live AI thinking stream widget that reads from thinking.jsonl."""

import json
from pathlib import Path
from datetime import datetime
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static, RichLog
from rich.text import Text
from rich.syntax import Syntax


class ThinkingStream(Widget):
    """Live stream of AI thinking events from thinking.jsonl."""

    DEFAULT_CSS = """
    ThinkingStream {
        height: 100%;
        background: $panel;
        border: tall $primary;
    }

    ThinkingStream .stream-header {
        height: 3;
        dock: top;
        background: $boost;
        color: $accent;
        text-style: bold;
        content-align: center middle;
        border-bottom: tall $primary;
    }

    ThinkingStream RichLog {
        background: $surface;
        color: $text;
        padding: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._thinking_file = Path.cwd() / "agent" / "state" / "thinking.jsonl"
        self._last_position = 0
        self._auto_scroll = True

    def compose(self) -> ComposeResult:
        """Compose the thinking stream layout."""
        yield Static("AI THINKING STREAM", classes="stream-header")
        yield RichLog(highlight=True, markup=True, id="thinking-log", auto_scroll=True)

    def on_mount(self) -> None:
        """Initialize when mounted."""
        self._load_initial_entries()

    def update_stream(self) -> None:
        """Read new entries from thinking.jsonl and display them."""
        if not self._thinking_file.exists():
            return

        try:
            with open(self._thinking_file, 'r', encoding='utf-8') as f:
                f.seek(self._last_position)
                new_content = f.read()
                self._last_position = f.tell()

            if not new_content.strip():
                return

            log_widget = self.query_one("#thinking-log", RichLog)

            for line in new_content.strip().split('\n'):
                if not line.strip():
                    continue

                try:
                    event = json.loads(line)
                    formatted = self._format_thinking_event(event)
                    if formatted:
                        log_widget.write(formatted)
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

        except Exception:
            pass

    def _load_initial_entries(self) -> None:
        """Load the last 50 entries from the thinking file."""
        if not self._thinking_file.exists():
            return

        try:
            with open(self._thinking_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                self._last_position = f.tell()

            log_widget = self.query_one("#thinking-log", RichLog)

            for line in lines[-50:]:
                if not line.strip():
                    continue

                try:
                    event = json.loads(line)
                    formatted = self._format_thinking_event(event)
                    if formatted:
                        log_widget.write(formatted)
                except (json.JSONDecodeError, Exception):
                    continue

        except Exception:
            pass

    def _format_thinking_event(self, event: dict) -> Text:
        """Format a thinking event for display with colors and icons."""
        event_type = event.get('event_type', 'unknown')
        data = event.get('data', {})
        cycle = event.get('cycle', 0)
        timestamp = event.get('timestamp', 0)

        dt = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        time_str = dt.strftime("%H:%M:%S")

        text = Text()
        text.append(f"[{time_str}] ", style="dim")
        text.append(f"C{cycle:03d} ", style="bold magenta")

        if event_type == 'cycle_start':
            cycle_num = data.get('cycle', '?')
            text.append("CYCLE START", style="bold cyan")
            text.append(f" Cycle {cycle_num}", style="white")

        elif event_type == 'cycle_end':
            cycle_num = data.get('cycle', '?')
            text.append("CYCLE END", style="bold green")
            text.append(f" Cycle {cycle_num}", style="white")

        elif event_type == 'thinking':
            thinking_type = data.get('type', 'general')
            content = data.get('content', '')
            text.append("THINKING ", style="bold yellow")
            text.append(f"[{thinking_type}] ", style="dim cyan")
            text.append(content, style="white")

        elif event_type == 'action':
            action = data.get('action', 'unknown')
            details = data.get('details', '')
            status = data.get('status', '')

            if status == "completed":
                text.append("ACTION DONE ", style="bold green")
            elif status == "started":
                text.append("ACTION START ", style="bold blue")
            elif status == "failed":
                text.append("ACTION FAIL ", style="bold red")
            else:
                text.append("ACTION ", style="bold blue")

            text.append(f"{action} ", style="cyan")
            if details:
                text.append(f"- {details}", style="white")

        elif event_type == 'decision':
            decision = data.get('decision', 'unknown')
            details = data.get('details', '')
            text.append("DECISION ", style="bold magenta")
            text.append(f"{decision} ", style="cyan")
            if details:
                text.append(f"- {details}", style="white")

        elif event_type == 'verification':
            tool = data.get('tool', 'unknown')
            result = data.get('result', 'unknown')
            details = data.get('details', '')
            text.append("VERIFY ", style="bold cyan")
            text.append(f"{tool} -> {result} ", style="yellow")
            if details:
                text.append(f"- {details}", style="white")

        elif event_type == 'model_interaction':
            model = data.get('model', 'unknown')
            interaction_type = data.get('interaction_type', 'unknown')
            details = data.get('details', '')
            text.append("MODEL ", style="bold blue")
            text.append(f"{model} ({interaction_type}) ", style="cyan")
            if details:
                text.append(f"- {details}", style="white")

        elif event_type == 'code_generation':
            language = data.get('language', 'unknown')
            details = data.get('details', '')
            text.append("CODE ", style="bold green")
            text.append(f"[{language}] ", style="cyan")
            if details:
                text.append(details, style="white")

        else:
            content = data.get('content', data.get('details', data.get('message', str(data))))
            text.append(f"{event_type.upper()} ", style="bold white")
            text.append(str(content), style="white")

        return text

    def clear(self) -> None:
        """Clear the thinking stream."""
        try:
            log_widget = self.query_one("#thinking-log", RichLog)
            log_widget.clear()
        except Exception:
            pass
