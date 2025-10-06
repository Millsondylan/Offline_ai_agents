"""Widget for displaying model thinking and reasoning process."""
from __future__ import annotations

from textual.containers import VerticalScroll
from textual.widgets import Static, RichLog, Label


class ThinkingLog(Static):
    """Displays the model's thinking process in real-time."""

    def __init__(self) -> None:
        super().__init__(id="thinking-log-widget")
        self.title = Label("═══ MODEL THINKING ═══", classes="panel-title")
        self.log = RichLog(highlight=True, markup=True, id="thinking-log-content")

    def compose(self):
        yield self.title
        with VerticalScroll(id="thinking-scroll"):
            yield self.log

    def add_thought(self, thought_type: str, content: str, metadata: dict = None) -> None:
        """Add a thought to the log.

        Args:
            thought_type: Type of thought (planning, reasoning, decision, action, etc.)
            content: The actual thought content
            metadata: Optional metadata about the thought
        """
        icons = {
            "planning": "📋",
            "reasoning": "🤔",
            "decision": "⚡",
            "action": "🔨",
            "reflection": "💭",
            "error": "❌",
            "success": "✅",
            "analysis": "🔍",
            "strategy": "🎯",
        }

        icon = icons.get(thought_type, "💡")
        timestamp = self._get_timestamp()

        self.log.write(f"[dim]{timestamp}[/dim] {icon} [bold cyan]{thought_type.upper()}[/bold cyan]")
        self.log.write(f"  {content}")

        if metadata:
            for key, value in metadata.items():
                self.log.write(f"  [dim]• {key}: {value}[/dim]")

        self.log.write("")  # Blank line for readability

    def add_step(self, step_num: int, step_name: str, status: str = "in_progress") -> None:
        """Add a step indicator to the log."""
        status_icons = {
            "in_progress": "⏳",
            "completed": "✅",
            "failed": "❌",
            "skipped": "⏭️",
        }

        icon = status_icons.get(status, "•")
        color = {
            "in_progress": "yellow",
            "completed": "green",
            "failed": "red",
            "skipped": "dim",
        }.get(status, "white")

        self.log.write(f"{icon} [bold {color}]Step {step_num}: {step_name}[/bold {color}]")

    def add_code_analysis(self, file_path: str, analysis: str) -> None:
        """Add code analysis thinking."""
        self.log.write(f"[bold cyan]📄 Analyzing:[/bold cyan] {file_path}")
        self.log.write(f"  {analysis}")
        self.log.write("")

    def add_verification(self, check_name: str, passed: bool, details: str = "") -> None:
        """Add verification check result."""
        icon = "✅" if passed else "❌"
        color = "green" if passed else "red"

        self.log.write(f"{icon} [bold {color}]Verification: {check_name}[/bold {color}]")
        if details:
            self.log.write(f"  {details}")
        self.log.write("")

    def add_model_response(self, prompt_summary: str, response_summary: str) -> None:
        """Add model interaction summary."""
        self.log.write("[bold magenta]🤖 Model Interaction[/bold magenta]")
        self.log.write(f"  [dim]Prompt:[/dim] {prompt_summary}")
        self.log.write(f"  [dim]Response:[/dim] {response_summary}")
        self.log.write("")

    def clear_log(self) -> None:
        """Clear all thinking logs."""
        self.log.clear()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
