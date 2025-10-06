"""Help panel."""

from agent_dashboard.panels.base import BasePanel


class HelpPanel(BasePanel):
    """Help/shortcuts panel."""

    def __init__(self, agent_manager, theme_manager):
        super().__init__("Help", agent_manager, theme_manager)

    def render(self, win, start_y: int, start_x: int, height: int, width: int):
        """Render help text."""
        y = start_y + 1
        x = start_x + 2

        shortcuts = [
            ("=== NAVIGATION ===", ""),
            ("1-9", "Jump to menu section"),
            ("↑/↓", "Navigate lists"),
            ("Enter", "Select/Confirm"),
            ("ESC", "Go back/Cancel"),
            ("", ""),
            ("=== AGENT CONTROL ===", ""),
            ("2", "Start/Pause/Resume agent"),
            ("3", "Stop agent"),
            ("Space", "Quick pause/resume"),
            ("", ""),
            ("=== TASKS (Panel 1) ===", ""),
            ("N", "New task"),
            ("D", "Delete selected task"),
            ("A", "Activate selected task"),
            ("", ""),
            ("=== THINKING (Panel 4) ===", ""),
            ("Home", "Jump to top"),
            ("End", "Jump to bottom (auto-scroll)"),
            ("", ""),
            ("=== LOGS (Panel 5) ===", ""),
            ("F", "Toggle error filter"),
            ("C", "Clear logs"),
            ("", ""),
            ("=== GLOBAL ===", ""),
            ("T/F1", "Toggle dark/light theme"),
            ("0/Q", "Exit application"),
        ]

        for key, desc in shortcuts:
            if y >= start_y + height - 1:
                break

            if not desc:  # Empty line
                y += 1
                continue

            if key.startswith("==="):  # Header
                self.safe_addstr(win, y, x, key,
                               self.theme_manager.get('highlight'))
            else:
                text = f"{key:10} {desc}"
                self.safe_addstr(win, y, x, text)
            y += 1

    def handle_key(self, key: int) -> bool:
        """Help panel doesn't handle keys."""
        return False
