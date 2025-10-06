"""Detail view screen for showing action progress and results."""
from __future__ import annotations

from textual.containers import Vertical, VerticalScroll
from textual.widgets import Label, Static, RichLog


class DetailView(Static):
    """Shows detailed information about an action being performed."""

    def __init__(self) -> None:
        super().__init__(id="detail-view")
        self.title = Label("", id="detail-title")
        self.status = Label("", id="detail-status")
        self.help_text = Label("Press ESC or 'q' to return to menu", id="detail-help")

    def compose(self):
        with Vertical(id="detail-container"):
            yield self.title
            yield self.status
            with VerticalScroll(id="detail-log-scroll"):
                yield RichLog(id="detail-log")
            yield self.help_text

    def _get_log(self) -> RichLog:
        """Get the RichLog widget."""
        try:
            return self.query_one("#detail-log", RichLog)
        except Exception:
            # Fallback if not mounted yet
            return None

    def show_action(self, action_name: str, status: str = "Working...") -> None:
        """Display an action with initial status."""
        self.title.update(f"═══ {action_name.upper()} ═══")
        self.status.update(f"Status: {status}")
        log = self._get_log()
        if log:
            log.clear()
            log.write(f"[bold cyan]{action_name}[/bold cyan]")
            log.write(f"Started at: {self._get_timestamp()}")
            log.write("")

    def update_status(self, status: str) -> None:
        """Update the status label."""
        self.status.update(f"Status: {status}")

    def add_log(self, message: str) -> None:
        """Add a log message."""
        log = self._get_log()
        if log:
            log.write(message)

    def show_success(self, message: str = "Action completed successfully") -> None:
        """Show success status."""
        self.status.update(f"Status: [bold green]✓ {message}[/bold green]")
        log = self._get_log()
        if log:
            log.write("")
            log.write(f"[bold green]✓ {message}[/bold green]")
            log.write(f"Completed at: {self._get_timestamp()}")

    def show_error(self, message: str) -> None:
        """Show error status."""
        self.status.update(f"Status: [bold red]✗ Error[/bold red]")
        log = self._get_log()
        if log:
            log.write("")
            log.write(f"[bold red]✗ Error: {message}[/bold red]")

    def show_task_details(self, task_id: str, task_title: str, status: str) -> None:
        """Show task details."""
        self.title.update(f"═══ TASK: {task_title} ═══")
        self.status.update(f"Status: {status}")
        log = self._get_log()
        if log:
            log.clear()
            log.write(f"[bold cyan]Task ID:[/bold cyan] {task_id}")
            log.write(f"[bold cyan]Title:[/bold cyan] {task_title}")
            log.write(f"[bold cyan]Status:[/bold cyan] {status}")
            log.write("")
            log.write("[dim]Toggling task status...[/dim]")

    def show_gate_details(self, gate_name: str, status: str, findings: str) -> None:
        """Show gate findings."""
        self.title.update(f"═══ GATE: {gate_name} ═══")
        status_icon = {"passed": "✓", "failed": "✗", "running": "⏳"}.get(status.lower(), "□")
        self.status.update(f"Status: {status_icon} {status}")
        log = self._get_log()
        if log:
            log.clear()
            log.write(f"[bold cyan]Gate:[/bold cyan] {gate_name}")
            log.write(f"[bold cyan]Status:[/bold cyan] {status}")
            log.write("")
            log.write("[bold]Findings:[/bold]")
            log.write(findings if findings else "[dim]No findings to display[/dim]")

    def show_artifact(self, artifact_name: str, content: str) -> None:
        """Show artifact contents."""
        self.title.update(f"═══ ARTIFACT: {artifact_name} ═══")
        self.status.update("Status: Viewing file")
        log = self._get_log()
        if log:
            log.clear()
            log.write(f"[bold cyan]File:[/bold cyan] {artifact_name}")
            log.write("")
            log.write("[bold]Contents:[/bold]")
            log.write(content if content else "[dim]Empty file[/dim]")

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
