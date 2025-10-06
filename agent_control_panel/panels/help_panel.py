"""Help panel."""

from agent_control_panel.panels.base_panel import BasePanel
from agent_control_panel.utils.keyboard import MappedKey


class HelpPanel(BasePanel):
    """Panel showing keyboard shortcuts."""

    def __init__(self, window, state_manager=None):
        super().__init__("Help", window, state_manager)

    def handle_key(self, key: MappedKey) -> bool:
        """Handle keyboard input."""
        return False

    def render(self) -> None:
        """Render help text."""
        self._render_title("Keyboard Shortcuts")

        shortcuts = [
            ("Global", ""),
            ("  1-9", "Switch to panel"),
            ("  ESC", "Go back"),
            ("  Ctrl+Q", "Quit application"),
            ("  Ctrl+R", "Refresh screen"),
            ("", ""),
            ("Tasks Panel", ""),
            ("  N", "New task"),
            ("  E", "Edit task"),
            ("  D", "Delete task"),
            ("  ↑↓", "Navigate"),
            ("", ""),
            ("Thinking/Logs", ""),
            ("  ↑↓", "Scroll"),
            ("  Home/End", "Jump to top/bottom"),
            ("  F", "Filter (logs only)"),
            ("  C", "Clear (logs only)"),
        ]

        y = 2
        for key, description in shortcuts:
            if not key:
                y += 1
                continue
            if not description:
                # Header
                self._safe_addstr(y, 2, key)
            else:
                self._safe_addstr(y, 2, f"{key:12} {description}")
            y += 1
