"""Simple, user-friendly TUI for the agent."""
from __future__ import annotations

from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Label
from textual.containers import Container, Vertical
from textual.binding import Binding


class SimpleTUI(App):
    """Simple TUI with clear instructions."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "run", "Run Cycle"),
        Binding("s", "status", "Show Status"),
        Binding("h", "help", "Help"),
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
                Static("[dim]Status: Waiting for commands...[/dim]", id="status-panel"),
                id="main-container"
            )
        )
        yield Footer()

    def action_run(self) -> None:
        """Run a cycle."""
        self.control_root.mkdir(parents=True, exist_ok=True)
        (self.control_root / "run_cycle.cmd").write_text("now")
        status = self.query_one("#status-panel", Static)
        status.update("[green]✓[/green] Cycle started! Check agent/artifacts/ for results.")

    def action_status(self) -> None:
        """Show status."""
        status = self.query_one("#status-panel", Static)
        state_root = Path(__file__).resolve().parent.parent / "state"
        if (state_root / "session.json").exists():
            import json
            session = json.loads((state_root / "session.json").read_text())
            status.update(f"[cyan]Status:[/cyan] {session.get('status', 'unknown')}\n"
                         f"[cyan]Cycle:[/cyan] {session.get('current_cycle', 0)}\n"
                         f"[cyan]Phase:[/cyan] {session.get('phase', 'idle')}")
        else:
            status.update("[yellow]No active session found. Press 'r' to start.[/yellow]")

    def action_help(self) -> None:
        """Show help."""
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


def launch_simple_tui() -> int:
    """Launch the simple TUI."""
    app = SimpleTUI()
    app.run()
    return 0
