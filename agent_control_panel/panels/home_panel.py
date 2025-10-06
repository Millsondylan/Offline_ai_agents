"""Home dashboard panel."""

import curses
from agent_control_panel.panels.base_panel import BasePanel
from agent_control_panel.utils.keyboard import Key, MappedKey


class HomePanel(BasePanel):
    """Dashboard panel showing overview."""

    def __init__(self, window, agent_controller, state_manager=None):
        super().__init__("Home", window, state_manager)
        self.agent_controller = agent_controller

    def handle_key(self, key: MappedKey) -> bool:
        """Handle keyboard input."""
        # Home doesn't handle keys, just displays
        return False

    def render(self) -> None:
        """Render the dashboard."""
        self._render_title("Agent Control Panel - Dashboard")

        status = self.agent_controller.get_status()

        # Render metrics
        y = 2
        self._safe_addstr(y, 2, f"Status: {status.state.value.upper()}", curses.A_BOLD)
        y += 2
        self._safe_addstr(y, 2, f"Model: {status.model_name}")
        y += 1
        self._safe_addstr(y, 2, f"Provider: {status.provider}")
        y += 1
        self._safe_addstr(y, 2, f"Cycle: {status.current_cycle}/{status.total_cycles}")
        y += 1
        self._safe_addstr(y, 2, f"Duration: {int(status.session_duration_seconds)}s")
        y += 2
        self._safe_addstr(y, 2, f"Thoughts: {status.thoughts_count}")
        y += 1
        self._safe_addstr(y, 2, f"Actions: {status.actions_count}")
