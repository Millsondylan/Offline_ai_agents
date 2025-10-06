"""Task input dialog for giving the agent work to do."""
from __future__ import annotations

from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Label, Button, TextArea, Input


class TaskInputDialog(Static):
    """Dialog for entering tasks/prompts for the agent."""

    def __init__(self) -> None:
        super().__init__(id="task-input-dialog")
        self.title = Label("═══ GIVE AGENT A TASK ═══", classes="panel-title")

    def compose(self):
        yield self.title

        yield Label("\n📋 What should the agent work on?", classes="section-label")
        yield Label("Be specific about what you want accomplished:", classes="help-text")

        yield TextArea(
            "Example:\n"
            "- Refactor the authentication module to use JWT tokens\n"
            "- Add error handling to the API endpoints\n"
            "- Write unit tests for the user service\n"
            "- Fix the bug in login.py where passwords aren't validated\n"
            "- Update documentation for the new features",
            id="task-input-textarea"
        )

        yield Label("\n⚙️ Configuration (optional):", classes="section-label")

        with Horizontal(id="task-config-row"):
            yield Label("Scope:")
            yield Input(placeholder="e.g., auth/, specific files", id="task-scope-input")
            yield Label("Max Cycles:")
            yield Input(placeholder="10", value="10", id="task-max-cycles-input")

        with Horizontal(id="task-action-buttons"):
            yield Button("🚀 Start Agent", id="start-agent-btn", variant="primary")
            yield Button("Cancel", id="cancel-task-btn")

        yield Label("", id="task-input-status")

        yield Label(
            "\n[dim]The agent will:\n"
            "  1. Read your task\n"
            "  2. Analyze the codebase\n"
            "  3. Run tests and linters\n"
            "  4. Generate changes\n"
            "  5. Apply patches\n"
            "  6. Run verification\n"
            "  7. Repeat until task is complete or max cycles reached[/dim]",
            id="task-help-text"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "start-agent-btn":
            self._start_agent_with_task()
        elif event.button.id == "cancel-task-btn":
            self._cancel()

    def _start_agent_with_task(self) -> None:
        """Start the agent with the entered task."""
        textarea = self.query_one("#task-input-textarea", TextArea)
        scope_input = self.query_one("#task-scope-input", Input)
        max_cycles_input = self.query_one("#task-max-cycles-input", Input)

        task_description = textarea.text.strip()
        scope = scope_input.value.strip()

        try:
            max_cycles = int(max_cycles_input.value or "10")
        except ValueError:
            self._show_status("Max cycles must be a number", error=True)
            return

        if not task_description or task_description.startswith("Example:"):
            self._show_status("Please enter a task description", error=True)
            return

        # Write task to file for agent to read
        if hasattr(self.app, "start_agent_with_task"):
            success = self.app.start_agent_with_task(task_description, scope, max_cycles)
            if success:
                self._show_status("✓ Agent started!", error=False)
                # Clear inputs
                textarea.text = ""
                scope_input.value = ""
            else:
                self._show_status("Failed to start agent", error=True)
        else:
            self._show_status("Agent not available", error=True)

    def _cancel(self) -> None:
        """Cancel and return to menu."""
        if hasattr(self.app, "show_menu"):
            self.app.show_menu()

    def _show_status(self, message: str, error: bool = False) -> None:
        """Show status message."""
        status = self.query_one("#task-input-status", Label)
        color = "red" if error else "green"
        status.update(f"[{color}]{message}[/{color}]")
