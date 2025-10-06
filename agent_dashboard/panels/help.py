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
            ("T/S/A/L/C/M/H", "Menu shortcuts"),
            ("↑/↓", "Navigate lists"),
            ("Enter", "Select/Confirm"),
            ("ESC", "Go back/Cancel"),
            ("", ""),
            ("=== MENU ===", ""),
            ("T", "Task Manager"),
            ("S", "Start/Pause agent"),
            ("X", "Stop agent"),
            ("A", "AI Thinking stream"),
            ("L", "Execution Logs"),
            ("C", "Code Viewer"),
            ("M", "Model Configuration"),
            ("H", "Help (this screen)"),
            ("", ""),
            ("=== TASKS ===", ""),
            ("N", "New task"),
            ("D", "Delete selected task"),
            ("A", "Activate selected task"),
            ("", ""),
            ("=== CODE VIEWER ===", ""),
            ("Enter", "View selected file"),
            ("R", "Refresh file list"),
            ("ESC", "Back to file list"),
            ("", ""),
            ("=== MODEL CONFIG ===", ""),
            ("Enter", "Select model"),
            ("R", "Refresh model list"),
            ("", ""),
            ("=== LOGS ===", ""),
            ("F", "Toggle error filter"),
            ("C", "Clear logs"),
            ("", ""),
            ("=== GLOBAL ===", ""),
            ("F1", "Toggle dark/light theme"),
            ("Q", "Exit application"),
            ("Space", "Quick pause/resume"),
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
