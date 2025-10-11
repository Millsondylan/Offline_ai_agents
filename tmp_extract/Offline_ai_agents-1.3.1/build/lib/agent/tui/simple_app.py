"""Simple, user-friendly TUI for the agent."""
from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Static


class SimpleTUI(App):
    """Simple TUI with clear instructions."""

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True, priority=True),
        Binding("r", "run", "Run Cycle", show=True, priority=True),
        Binding("s", "status", "Show Status", show=True, priority=True),
        Binding("h", "help", "Help", show=True, priority=True),
    ]

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
        padding: 2;
    }

    #welcome {
        border: heavy $primary;
        padding: 2;
        margin: 1;
        height: auto;
    }

    #instructions {
        border: solid $secondary;
        padding: 2;
        margin: 1;
        height: auto;
    }

    #status-panel {
        border: solid $accent;
        padding: 1;
        margin: 1;
        height: 1fr;
    }

    .title {
        text-style: bold;
        color: $accent;
        text-align: center;
    }

    .help-text {
        color: $text;
        padding: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.control_root = Path(__file__).resolve().parent.parent / "local" / "control"
        self.state_root = Path(__file__).resolve().parent.parent / "state"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Vertical(
                Static("[bold cyan]🤖 Agent TUI[/bold cyan]", id="welcome", classes="title"),
                Static(
                    """
[bold]Quick Start Guide[/bold]

Press the following keys to control the agent:

  [cyan]r[/cyan] - Run a cycle (starts the agent)
  [cyan]s[/cyan] - Show current status
  [cyan]h[/cyan] - Show this help
  [cyan]q[/cyan] - Quit

[bold]What is this?[/bold]

This is the Terminal User Interface (TUI) for the autonomous coding agent.
The agent watches your code, suggests improvements, and runs safety checks.

[bold]Getting Started:[/bold]

1. Press 'r' to run your first cycle
2. The agent will analyze your code and suggest changes
3. Review suggestions and approve/reject them
4. Press 's' to check status anytime

[dim]Note: Agent state will appear below once a cycle starts[/dim]
                    """,
                    id="instructions",
                    classes="help-text"
                ),
                Static("[dim]Status: Waiting for commands... (Press a key to test)[/dim]", id="status-panel"),
                id="main-container"
            )
        )
        yield Footer()

    def on_key(self, event) -> None:
        """Debug: Show which key was pressed."""
        status = self.query_one("#status-panel", Static)
        status.update(f"[yellow]Key pressed: {event.key}[/yellow]")

    def action_run(self) -> None:
        """Run a cycle."""
        try:
            self.control_root.mkdir(parents=True, exist_ok=True)
            (self.control_root / "run_cycle.cmd").write_text("now")
            status = self.query_one("#status-panel", Static)
            status.update("[green]✓[/green] Cycle started! Check agent/artifacts/ for results.")
        except Exception as e:
            status = self.query_one("#status-panel", Static)
            status.update(f"[red]Error:[/red] {e}")

    def action_status(self) -> None:
        """Show status."""
        try:
            status = self.query_one("#status-panel", Static)
            if (self.state_root / "session.json").exists():
                import json
                session = json.loads((self.state_root / "session.json").read_text())
                status.update(f"[cyan]Status:[/cyan] {session.get('status', 'unknown')}\n"
                             f"[cyan]Cycle:[/cyan] {session.get('current_cycle', 0)}\n"
                             f"[cyan]Phase:[/cyan] {session.get('phase', 'idle')}")
            else:
                status.update("[yellow]No active session found. Press 'r' to start.[/yellow]")
        except Exception as e:
            status = self.query_one("#status-panel", Static)
            status.update(f"[red]Error:[/red] {e}")

    def action_help(self) -> None:
        """Show help."""
        try:
            status = self.query_one("#status-panel", Static)
            status.update(
                """[bold cyan]Command Reference:[/bold cyan]

[cyan]r[/cyan] - Run Cycle: Starts a new agent cycle
[cyan]s[/cyan] - Status: Shows current agent state
[cyan]h[/cyan] - Help: Shows this help text
[cyan]q[/cyan] - Quit: Exit the TUI

[bold]More Info:[/bold]
- Agent runs in background as brew service
- Control files: agent/local/control/
- State files: agent/state/
- Artifacts: agent/artifacts/
            """
            )
        except Exception as e:
            status = self.query_one("#status-panel", Static)
            status.update(f"[red]Error:[/red] {e}")


def launch_simple_tui() -> int:
    """Launch the simple TUI."""
    app = SimpleTUI()
    app.run()
    return 0
