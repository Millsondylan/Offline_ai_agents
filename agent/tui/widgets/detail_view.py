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
        self.log = RichLog(id="detail-log", wrap=True, highlight=True, markup=True)
        self.help_text = Label("Press ESC or 'q' to return to menu", id="detail-help")

    def compose(self):
        yield Vertical(
            self.title,
            self.status,
            VerticalScroll(self.log, id="detail-log-scroll"),
            self.help_text,
            id="detail-container"
        )

    def show_action(self, action_name: str, status: str = "Working...") -> None:
        """Display an action with initial status."""
        self.title.update(f"═══ {action_name.upper()} ═══")
        self.status.update(f"Status: {status}")
        self.log.clear()
        self.log.write(f"[bold cyan]{action_name}[/bold cyan]")
        self.log.write(f"Started at: {self._get_timestamp()}")
        self.log.write("")

    def update_status(self, status: str) -> None:
        """Update the status label."""
        self.status.update(f"Status: {status}")

    def add_log(self, message: str) -> None:
        """Add a log message."""
        self.log.write(message)

    def show_success(self, message: str = "Action completed successfully") -> None:
        """Show success status."""
        self.status.update(f"Status: [bold green]✓ {message}[/bold green]")
        self.log.write("")
        self.log.write(f"[bold green]✓ {message}[/bold green]")
        self.log.write(f"Completed at: {self._get_timestamp()}")

    def show_error(self, message: str) -> None:
        """Show error status."""
        self.status.update(f"Status: [bold red]✗ Error[/bold red]")
        self.log.write("")
        self.log.write(f"[bold red]✗ Error: {message}[/bold red]")

    def show_task_details(self, task_id: str, task_title: str, status: str) -> None:
        """Show task details."""
        self.title.update(f"═══ TASK: {task_title} ═══")
        self.status.update(f"Status: {status}")
        self.log.clear()
        self.log.write(f"[bold cyan]Task ID:[/bold cyan] {task_id}")
        self.log.write(f"[bold cyan]Title:[/bold cyan] {task_title}")
        self.log.write(f"[bold cyan]Status:[/bold cyan] {status}")
        self.log.write("")
        self.log.write("[dim]Toggling task status...[/dim]")

    def show_gate_details(self, gate_name: str, status: str, findings: str) -> None:
        """Show gate findings."""
        self.title.update(f"═══ GATE: {gate_name} ═══")
        status_icon = {"passed": "✓", "failed": "✗", "running": "⏳"}.get(status.lower(), "□")
        self.status.update(f"Status: {status_icon} {status}")
        self.log.clear()
        self.log.write(f"[bold cyan]Gate:[/bold cyan] {gate_name}")
        self.log.write(f"[bold cyan]Status:[/bold cyan] {status}")
        self.log.write("")
        self.log.write("[bold]Findings:[/bold]")
        self.log.write(findings if findings else "[dim]No findings to display[/dim]")

    def show_artifact(self, artifact_name: str, content: str) -> None:
        """Show artifact contents."""
        self.title.update(f"═══ ARTIFACT: {artifact_name} ═══")
        self.status.update("Status: Viewing file")
        self.log.clear()
        self.log.write(f"[bold cyan]File:[/bold cyan] {artifact_name}")
        self.log.write("")
        self.log.write("[bold]Contents:[/bold]")
        self.log.write(content if content else "[dim]Empty file[/dim]")

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
