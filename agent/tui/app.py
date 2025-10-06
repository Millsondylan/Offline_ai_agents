from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical

from .navigation import NavEntry, NavigationHint, NavigationManager
from .state_watcher import ArtifactState, StateWatcher
from .widgets.artifact_browser import ArtifactBrowser
from .widgets.cycle_info import CycleInfoPanel
from .widgets.gate_status import GateStatusPanel
from .widgets.control_panel import ControlPanel
from .widgets.output_viewer import OutputViewer
from .widgets.status_bar import StatusBar
from .widgets.task_queue import TaskQueue


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
        self.status_bar = StatusBar()
        self._status_timer = None
        self.control_root = Path(__file__).resolve().parent.parent / "local" / "control"
        self.config_path = Path(__file__).resolve().parent.parent / "config.json"

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(self.control_panel, self.cycle_panel, id="row-top"),
            Horizontal(self.task_queue, self.gate_panel, self.artifact_browser, id="row-middle"),
            self.output_viewer,
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
            self.control_panel.pause_button,
            self.control_panel.stop_button,
            self.control_panel.model_button,
            self.control_panel.commit_button,
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
    # Control helpers
    # ------------------------------------------------------------------

    def pause_agent(self) -> None:
        self._write_control("pause")
        self.show_status("Pause command sent")

    def resume_agent(self) -> None:
        self._write_control("resume")
        self.show_status("Resume command sent")

    def stop_agent(self) -> None:
        self._write_control("stop")
        self.show_status("Stop command sent")

    def force_commit(self) -> None:
        self._write_control("commit")
        self.show_status("Force commit command sent")

    def switch_model(self, model: str) -> None:
        safe = model.lower().replace(" ", "_")
        self._write_control(f"switch_model_{safe}")
        self.show_status(f"Switching model to {model}")

    def toggle_task(self, task_id: str) -> None:
        payload = f"toggle {task_id}"
        self._write_control("task_control", payload)
        self.show_status(f"Toggled task {task_id}")

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
        self.output_viewer.filter_findings(gate_name)
        self.output_viewer.select_tab("findings")
        self.show_status(f"Viewing findings for {gate_name}")

    def open_artifact(self, artifact: ArtifactState) -> None:
        try:
            self.output_viewer.load_artifact(artifact)
            self.show_status(f"Opened {artifact.label}")
        except Exception as exc:  # pragma: no cover - defensive
            self.show_status(f"Failed to open artifact: {exc}")

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


def launch_app() -> int:
    app = AgentTUI()
    app.run()
    return 0
