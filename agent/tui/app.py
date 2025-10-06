from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Label

from .navigation import NavEntry, NavigationHint, NavigationManager
from .state_watcher import ArtifactState, StateWatcher
from .widgets.artifact_browser import ArtifactBrowser
from .widgets.cycle_info import CycleInfoPanel
from .widgets.gate_status import GateStatusPanel
from .widgets.control_panel import ControlPanel
from .widgets.detail_view import DetailView
from .widgets.output_viewer import OutputViewer
from .widgets.status_bar import StatusBar
from .widgets.task_queue import TaskQueue
from .widgets.thinking_log import ThinkingLog
from .widgets.model_selector import ModelSelector
from .widgets.verification_config import VerificationConfig
from .widgets.task_manager import TaskManager


class AgentTUI(App[None]):
    """Main Textual application orchestrating the autonomous agent dashboard."""

    CSS_PATH = Path(__file__).with_name("styles.css")

    # Ensure app can receive keyboard events
    can_focus = True

    BINDINGS = [
        Binding("up,k", "focus_previous", "Previous", priority=True),
        Binding("down,j", "focus_next", "Next", priority=True),
        Binding("enter,space", "activate", "Activate", priority=True),
        Binding("escape,q", "quit_app", "Exit", priority=True),
        Binding("1", "jump_to", "Jump to 1", priority=True),
        Binding("2", "jump_to", "Jump to 2", priority=True),
        Binding("3", "jump_to", "Jump to 3", priority=True),
        Binding("4", "jump_to", "Jump to 4", priority=True),
        Binding("5", "jump_to", "Jump to 5", priority=True),
        Binding("6", "jump_to", "Jump to 6", priority=True),
        Binding("7", "jump_to", "Jump to 7", priority=True),
        Binding("8", "jump_to", "Jump to 8", priority=True),
        Binding("9", "jump_to", "Jump to 9", priority=True),
        Binding("0", "jump_to", "Jump to 10", priority=True),
        Binding("h,question_mark", "show_help", "Help", priority=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.state_watcher = StateWatcher()
        self.navigation = NavigationManager(self, on_focus_change=self._on_focus_change)
        self.control_panel = ControlPanel()
        self.cycle_panel = CycleInfoPanel()
        self.task_queue = TaskQueue()
        self.gate_panel = GateStatusPanel()
        self.artifact_browser = ArtifactBrowser()
        self.output_viewer = OutputViewer()
        self.detail_view = DetailView()
        self.status_bar = StatusBar()
        self.thinking_log = ThinkingLog()
        self.model_selector = ModelSelector()
        self.verification_config = VerificationConfig()
        self.task_manager = TaskManager()
        self._status_timer = None
        self._in_detail_mode = False
        self.control_root = Path(__file__).resolve().parent.parent / "local" / "control"
        self.config_path = Path(__file__).resolve().parent.parent / "config.json"

        # Initialize task executor
        from ..task_executor import TaskExecutor
        state_root = Path(__file__).resolve().parent.parent / "state" / "tasks"
        state_root.mkdir(parents=True, exist_ok=True)
        self.task_executor = TaskExecutor(state_root)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        self.menu_container = Vertical(
            Label("AGENT DASHBOARD", classes="panel-title"),
            Horizontal(self.control_panel, self.cycle_panel, id="row-top"),
            Label("\n" + "═" * 80 + "\nMENU - Press number to jump, ↑↓/jk to navigate, ENTER/SPACE to select\n" + "═" * 80, id="menu-header"),
            Vertical(
                self.task_queue,
                self.gate_panel,
                self.artifact_browser,
                id="menu-section"
            ),
            id="menu-container"
        )

        # Detail view starts hidden
        self.detail_view.display = False

        yield Vertical(
            self.menu_container,
            self.detail_view,
            self.status_bar,
            id="layout-root",
        )

    async def on_mount(self) -> None:
        # Load test data if state directory is empty
        session_file = self.state_watcher.state_root / "session.json"
        if not session_file.exists():
            self.show_status("Loading test data...")
            try:
                from .test_data_generator import generate_test_data
                generate_test_data()
                self.show_status("Test data loaded - navigate with ↑↓ arrows")
            except Exception as e:
                self.show_status(f"Note: No test data - {e}")

        await self.poll_state()
        self.set_interval(0.5, self.poll_state)
        self.rebuild_navigation()

        # Focus the app so it receives keyboard events
        self.set_focus(None)

        # Apply initial focus after everything is mounted
        if self.navigation.entries:
            self.navigation._apply_focus()

        # Show initial status
        entry_count = len(self.navigation.entries)
        self.show_status(f"Ready! {entry_count} items. Use ↑↓ to navigate, ENTER to activate, ESC to exit.")

    # ------------------------------------------------------------------
    # Input & navigation handling
    # ------------------------------------------------------------------

    async def on_key(self, event: events.Key) -> None:
        """Handle all key presses."""
        # In detail mode, only ESC/q work to go back
        if self._in_detail_mode:
            if event.key in ("escape", "q"):
                event.prevent_default()
                event.stop()
                self.show_menu()
            return

        # Vim-style navigation
        if event.key in ("up", "k"):
            event.prevent_default()
            event.stop()
            self.navigation.focus_previous()
        elif event.key in ("down", "j"):
            event.prevent_default()
            event.stop()
            self.navigation.focus_next()
        elif event.key in ("enter", "space"):
            event.prevent_default()
            event.stop()
            self.navigation.activate_focused()
        elif event.key in ("escape", "q"):
            event.prevent_default()
            event.stop()
            self.show_status("Exiting...")
            self.stop_agent()
            self.exit()
        # Number keys for direct jump
        elif event.key in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0"):
            event.prevent_default()
            event.stop()
            num = 10 if event.key == "0" else int(event.key)
            self.navigation.jump_to_index(num - 1)
        # Help
        elif event.key in ("h", "question_mark"):
            event.prevent_default()
            event.stop()
            self.show_help()

    def action_focus_next(self) -> None:
        """Move to next focusable element."""
        self.show_status("Down pressed")
        self.navigation.focus_next()

    def action_focus_previous(self) -> None:
        """Move to previous focusable element."""
        self.show_status("Up pressed")
        self.navigation.focus_previous()

    def action_activate(self) -> None:
        """Activate currently focused element."""
        self.show_status("Enter pressed")
        self.navigation.activate_focused()

    def action_quit_app(self) -> None:
        """Stop agent and exit."""
        self.show_status("Escape pressed")
        self.stop_agent()
        self.exit()

    async def on_navigation_hint(self, message: NavigationHint) -> None:
        self.status_bar.update_action(message.action)

    def _on_focus_change(self, entry: Optional[NavEntry]) -> None:
        self.status_bar.update_action(entry.action if entry else None)

    def _build_navigation_order(self) -> List[NavEntry]:
        entries: List[NavEntry] = []
        buttons = [
            self.control_panel.start_button,
            self.control_panel.pause_button,
            self.control_panel.stop_button,
            self.control_panel.task_manager_button,
            self.control_panel.thinking_button,
            self.control_panel.model_config_button,
            self.control_panel.verification_button,
            self.control_panel.model_button,
            self.control_panel.commit_button,
            self.control_panel.logs_button,
        ]
        for button in buttons:
            if button.id:
                entries.append(NavEntry(widget_id=button.id, action=button.enter_action))
        entries.extend(self.task_queue.nav_entries())
        entries.extend(self.gate_panel.nav_entries())
        entries.extend(self.artifact_browser.nav_entries())
        entries.extend(self.output_viewer.nav_entries())
        return entries

    def rebuild_navigation(self) -> None:
        entries = self._build_navigation_order()
        self.navigation.set_entries(entries)

        # Add visible numbers to first 10 items
        for i, entry in enumerate(entries[:10]):
            try:
                widget = self.query_one(f"#{entry.widget_id}")
                if hasattr(widget, "set_display"):
                    display_num = i + 1 if i < 9 else 0
                    # Get current label without any existing number prefix
                    current_label = str(widget.label)
                    # Remove existing [digit] prefix if present
                    current_label = re.sub(r'^\[\d\]\s*', '', current_label)
                    widget.set_display(f"[{display_num}] {current_label}")
            except Exception:
                pass  # Widget might not exist yet

        # Ensure something is focused initially
        if entries and self.navigation.current_index == 0:
            self.navigation._apply_focus()

    # ------------------------------------------------------------------
    # State polling & updates
    # ------------------------------------------------------------------

    async def poll_state(self) -> None:
        snapshot = self.state_watcher.snapshot()
        self.control_panel.update_state(snapshot.control)
        self.cycle_panel.update_state(snapshot.cycle)
        self.task_queue.update_tasks(snapshot.tasks)
        self.gate_panel.update_gates(snapshot.gates)
        self.artifact_browser.update_artifacts(snapshot.artifacts)
        self.output_viewer.update_diff(snapshot.output.diff_text)
        self.output_viewer.update_findings(snapshot.output.findings)
        self.output_viewer.update_logs(snapshot.output.logs)
        self.output_viewer.update_config(snapshot.output.config_text)
        self.rebuild_navigation()

    # ------------------------------------------------------------------
    # View mode switching
    # ------------------------------------------------------------------

    def show_menu(self) -> None:
        """Show the main menu and hide detail view."""
        self._in_detail_mode = False
        self.menu_container.display = True
        self.detail_view.display = False
        self.show_status("Returned to menu")

    def show_detail(self, action_name: str, status: str = "Working...") -> None:
        """Show detail view and hide menu."""
        self._in_detail_mode = True
        self.menu_container.display = False
        self.detail_view.display = True
        self.detail_view.show_action(action_name, status)

    # ------------------------------------------------------------------
    # Control helpers
    # ------------------------------------------------------------------

    def start_agent(self) -> None:
        self.show_detail("Start Agent")
        self.detail_view.add_log("Sending start command to agent...")
        self._write_control("start")
        self.detail_view.add_log("✓ Start command sent")
        self.detail_view.add_log("")
        self.detail_view.add_log("The agent will begin autonomous operation.")
        self.detail_view.add_log("Check the dashboard for progress updates.")
        self.detail_view.show_success("Agent started")

    def pause_agent(self) -> None:
        self.show_detail("Pause Agent")
        self.detail_view.add_log("Sending pause command to agent...")
        self._write_control("pause")
        self.detail_view.add_log("✓ Pause command sent")
        self.detail_view.add_log("")
        self.detail_view.add_log("The agent will stop after completing the current operation.")
        self.detail_view.show_success("Agent paused")

    def resume_agent(self) -> None:
        self.show_detail("Resume Agent")
        self.detail_view.add_log("Sending resume command to agent...")
        self._write_control("resume")
        self.detail_view.add_log("✓ Resume command sent")
        self.detail_view.add_log("")
        self.detail_view.add_log("The agent will continue from where it paused.")
        self.detail_view.show_success("Agent resumed")

    def stop_agent(self) -> None:
        self.show_detail("Stop Agent")
        self.detail_view.add_log("Sending stop command to agent...")
        self._write_control("stop")
        self.detail_view.add_log("✓ Stop command sent")
        self.detail_view.add_log("")
        self.detail_view.add_log("The agent will terminate all operations.")
        self.detail_view.add_log("[bold yellow]Note: Any in-progress tasks will be interrupted.[/bold yellow]")
        self.detail_view.show_success("Agent stopped")

    def force_commit(self) -> None:
        self.show_detail("Force Commit")
        self.detail_view.add_log("Sending force commit command...")
        self._write_control("commit")
        self.detail_view.add_log("✓ Commit command sent")
        self.detail_view.add_log("")
        self.detail_view.add_log("All pending changes will be committed to version control.")
        self.detail_view.show_success("Commit initiated")

    def switch_model(self, model: str) -> None:
        self.show_detail(f"Switch Model to {model}")
        self.detail_view.add_log(f"Switching AI model to: [bold cyan]{model}[/bold cyan]")
        safe = model.lower().replace(" ", "_")
        self._write_control(f"switch_model_{safe}")
        self.detail_view.add_log("✓ Model switch command sent")
        self.detail_view.add_log("")
        self.detail_view.add_log("The agent will use this model for future operations.")
        self.detail_view.show_success(f"Switched to {model}")

    def toggle_task(self, task_id: str) -> None:
        # Find task details from state
        snapshot = self.state_watcher.snapshot()
        task = next((t for t in snapshot.tasks if t.identifier == task_id), None)
        if task:
            self.detail_view.show_task_details(task_id, task.title, task.status)
        else:
            self.show_detail("Toggle Task")
            self.detail_view.add_log(f"Task ID: {task_id}")

        self.detail_view.add_log("")
        payload = f"toggle {task_id}"
        self._write_control("task_control", payload)
        self.detail_view.add_log("✓ Task toggle command sent")
        self.detail_view.show_success("Task status updated")

    def create_task(self, task_name: str) -> None:
        self._write_control("add_task", task_name)
        self.show_status(f"Queued task: {task_name}")

    def apply_all_diffs(self) -> None:
        self._write_control("apply_all_diffs")
        self.show_status("Applying all diffs…")

    def reject_all_diffs(self) -> None:
        self._write_control("reject_all_diffs")
        self.show_status("Rejecting all diffs…")

    def select_gate(self, gate_name: str) -> None:
        # Find gate details from state
        snapshot = self.state_watcher.snapshot()
        gate = next((g for g in snapshot.gates if g.name == gate_name), None)

        findings_text = snapshot.output.findings if snapshot.output.findings else "No findings available"

        if gate:
            self.detail_view.show_gate_details(gate.name, gate.status, findings_text)
        else:
            self.show_detail(f"Gate: {gate_name}")
            self.detail_view.add_log(findings_text)

    def open_artifact(self, artifact: ArtifactState) -> None:
        try:
            # Read artifact content
            content = artifact.path.read_text(encoding="utf-8") if artifact.path.exists() else "[File not found]"
            self.detail_view.show_artifact(artifact.label, content)
        except Exception as exc:  # pragma: no cover - defensive
            self.show_detail(f"Artifact: {artifact.label}")
            self.detail_view.show_error(f"Failed to load artifact: {exc}")

    def open_logs(self) -> None:
        """Open the logs viewer tab."""
        snapshot = self.state_watcher.snapshot()
        self.show_detail("Agent Logs")
        self.detail_view.add_log("[bold]Recent Logs:[/bold]")
        self.detail_view.add_log("")
        logs = snapshot.output.logs if snapshot.output.logs else "No logs available"
        self.detail_view.add_log(logs)

    def save_config(self, config: dict) -> None:
        text = json.dumps(config, indent=2, sort_keys=True)
        self.config_path.write_text(text, encoding="utf-8")
        self.output_viewer.update_config(text)
        self.show_status("Config saved")

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _write_control(self, name: str, content: str = "") -> None:
        self.control_root.mkdir(parents=True, exist_ok=True)
        path = self.control_root / f"{name}.cmd"
        path.write_text(content, encoding="utf-8")

    def show_status(self, message: str, duration: float = 3.0) -> None:
        self.status_bar.update_action(message)
        if self._status_timer is not None:
            self._status_timer.stop()
        self._status_timer = self.set_timer(duration, self._reset_status)

    def _reset_status(self) -> None:
        self.status_bar.update_action(None)
        self._status_timer = None

    def show_help(self) -> None:
        """Show keyboard shortcuts."""
        help_text = (
            "KEYBOARD SHORTCUTS:\n"
            "  1-9,0   Jump to item by number\n"
            "  ↑/k     Move up\n"
            "  ↓/j     Move down\n"
            "  ENTER   Execute/Select\n"
            "  SPACE   Execute/Select\n"
            "  q/ESC   Quit\n"
            "  h/?     This help"
        )
        self.show_status(help_text, duration=10.0)

    # ------------------------------------------------------------------
    # New Feature Methods
    # ------------------------------------------------------------------

    def open_task_manager(self) -> None:
        """Open the task management interface."""
        self.show_detail("Task Manager")
        self.detail_view.add_log("[bold cyan]Task Execution Manager[/bold cyan]")
        self.detail_view.add_log("")
        self.detail_view.add_log("Create and manage execution tasks with comprehensive verification:")
        self.detail_view.add_log("• Define tasks with custom time limits and verification counts")
        self.detail_view.add_log("• Track execution progress in real-time")
        self.detail_view.add_log("• View detailed verification results")
        self.detail_view.add_log("")
        self.detail_view.add_log("[dim]Use the task manager to create new execution tasks from the menu.[/dim]")

    def open_thinking_log(self) -> None:
        """Open the model thinking log viewer."""
        self.show_detail("Model Thinking Log")
        self.detail_view.add_log("[bold cyan]AI Model Reasoning Process[/bold cyan]")
        self.detail_view.add_log("")
        self.detail_view.add_log("This view shows the model's thinking process including:")
        self.detail_view.add_log("• Planning and strategy decisions")
        self.detail_view.add_log("• Code analysis and reasoning")
        self.detail_view.add_log("• Verification check results")
        self.detail_view.add_log("• Model responses and interactions")
        self.detail_view.add_log("")
        self.detail_view.add_log("[dim]The thinking log updates in real-time during task execution.[/dim]")

    def open_model_config(self) -> None:
        """Open model configuration interface."""
        self.show_detail("Model Configuration")
        self.detail_view.add_log("[bold cyan]AI Model Configuration[/bold cyan]")
        self.detail_view.add_log("")

        # Show available models from config
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
                available_models = config.get("available_models", [])
                current_model = config.get("provider", {}).get("model", "unknown")

                self.detail_view.add_log(f"[bold]Current Model:[/bold] {current_model}")
                self.detail_view.add_log("")
                self.detail_view.add_log("[bold]Available Models:[/bold]")
                for model in available_models:
                    marker = "→" if model == current_model else " "
                    self.detail_view.add_log(f"  {marker} {model}")
        except Exception as e:
            self.detail_view.add_log(f"[red]Error loading configuration: {e}[/red]")

        self.detail_view.add_log("")
        self.detail_view.add_log("[bold]Features:[/bold]")
        self.detail_view.add_log("• Switch between offline and API models")
        self.detail_view.add_log("• Configure API keys securely")
        self.detail_view.add_log("• Download new models (Ollama)")

    def open_verification_config(self) -> None:
        """Open verification configuration interface."""
        self.show_detail("Verification Configuration")
        self.detail_view.add_log("[bold cyan]Verification Checks Configuration[/bold cyan]")
        self.detail_view.add_log("")
        self.detail_view.add_log("Configure comprehensive quality checks:")
        self.detail_view.add_log("")
        self.detail_view.add_log("[bold red]CRITICAL CHECKS[/bold red] (Must Pass):")
        self.detail_view.add_log("  ✓ Syntax Validation")
        self.detail_view.add_log("  ✓ Import Validation")
        self.detail_view.add_log("  ✓ Test Suite Execution")
        self.detail_view.add_log("  ✓ Security Scanning")
        self.detail_view.add_log("  ✓ Build Verification")
        self.detail_view.add_log("")
        self.detail_view.add_log("[bold yellow]HIGH PRIORITY CHECKS[/bold yellow]:")
        self.detail_view.add_log("  • Linter Checks (Ruff)")
        self.detail_view.add_log("  • Type Checking")
        self.detail_view.add_log("  • Code Coverage")
        self.detail_view.add_log("  • Dependency Audit")
        self.detail_view.add_log("")
        self.detail_view.add_log("[bold blue]MEDIUM/LOW PRIORITY[/bold blue]:")
        self.detail_view.add_log("  • Code Formatting")
        self.detail_view.add_log("  • Documentation (Docstrings)")
        self.detail_view.add_log("  • Performance Baseline")
        self.detail_view.add_log("")
        self.detail_view.add_log("[dim]Customize time limits and verification counts as needed.[/dim]")

    def create_execution_task(self, task_name: str, description: str, max_duration: int, max_verifications: int) -> str:
        """Create a new execution task."""
        task_id = self.task_executor.create_task(
            task_name=task_name,
            description=description,
            max_duration=max_duration,
            max_verifications=max_verifications,
        )
        self.show_status(f"Task '{task_name}' created with ID {task_id}")
        return task_id

    def view_task_execution(self, task_id: str) -> None:
        """View details of a task execution."""
        task = self.task_executor.get_task(task_id)
        if not task:
            self.show_status(f"Task {task_id} not found", duration=3.0)
            return

        self.show_detail(f"Task: {task.task_name}")
        self.detail_view.add_log(f"[bold cyan]Task ID:[/bold cyan] {task_id}")
        self.detail_view.add_log(f"[bold cyan]Name:[/bold cyan] {task.task_name}")
        self.detail_view.add_log(f"[bold cyan]Description:[/bold cyan] {task.description}")
        self.detail_view.add_log(f"[bold cyan]Status:[/bold cyan] {task.status.value}")
        self.detail_view.add_log(f"[bold cyan]Progress:[/bold cyan] {task.progress:.1f}%")
        self.detail_view.add_log("")
        self.detail_view.add_log(f"[bold]Verifications:[/bold] {task.verification_passed}/{task.verification_total} passed")
        if task.verification_failed > 0:
            self.detail_view.add_log(f"[red]Failed: {task.verification_failed}[/red]")

        if task.verification_results:
            self.detail_view.add_log("")
            self.detail_view.add_log("[bold]Verification Details:[/bold]")
            for result in task.verification_results[-10:]:  # Show last 10
                icon = "✅" if result.passed else "❌"
                self.detail_view.add_log(f"  {icon} {result.check_id}: {result.message}")

    def cancel_execution_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        return self.task_executor.cancel_task(task_id)

    def configure_verification(self, max_verifications: int, max_duration: int, enabled_checks: List[str]) -> None:
        """Configure verification settings."""
        self.task_executor.configure_checks(
            max_verifications=max_verifications,
            max_duration=max_duration,
            enabled_checks=enabled_checks,
        )
        self.show_status(f"Verification configured: {len(enabled_checks)} checks enabled")

    def download_model(self, model_name: str) -> None:
        """Download a model (for offline providers like Ollama)."""
        self.show_detail(f"Downloading Model: {model_name}")
        self.detail_view.add_log(f"Starting download of model: [bold cyan]{model_name}[/bold cyan]")
        self.detail_view.add_log("")
        self.detail_view.add_log("[yellow]This may take several minutes depending on model size...[/yellow]")
        self.detail_view.add_log("")
        self.detail_view.add_log("[dim]The download will continue in the background.[/dim]")
        self.detail_view.add_log("[dim]Check your terminal for download progress.[/dim]")

        # Trigger download via control file
        self._write_control("download_model", model_name)


def launch_app() -> int:
    app = AgentTUI()
    app.run()
    return 0
