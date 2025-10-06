"""Home dashboard panel."""

from agent_dashboard.panels.base import BasePanel


class HomePanel(BasePanel):
    """Home dashboard showing welcome and overview."""

    def render(self, win, start_y: int, start_x: int, height: int, width: int):
        """Render home dashboard."""
        state = self.agent_manager.get_state()

        y = start_y + 2
        x = start_x + 2

        # Welcome message
        self.safe_addstr(win, y, x, "┌─ Welcome to Agent Control Panel ─┐",
                        self.theme_manager.get('highlight'))
        y += 1
        self.safe_addstr(win, y, x, "│                                   │")
        y += 1

        # Current status
        if state.current_task:
            self.safe_addstr(win, y, x, f"│ Active Task: {state.current_task[:16]:<16} │")
        else:
            self.safe_addstr(win, y, x, "│ No active task                    │")
        y += 1

        self.safe_addstr(win, y, x, f"│ Status: {state.status.value:8}              │",
                        self.theme_manager.get('running' if state.status.value == 'RUNNING' else 'normal'))
        y += 1
        self.safe_addstr(win, y, x, "│                                   │")
        y += 1
        self.safe_addstr(win, y, x, "└───────────────────────────────────┘")
        y += 2

        # Instructions
        self.safe_addstr(win, y, x, "Quick Start:", self.theme_manager.get('info'))
        y += 1
        self.safe_addstr(win, y, x, "1. Press 1 to manage tasks")
        y += 1
        self.safe_addstr(win, y, x, "2. Press 2 to start the agent")
        y += 1
        self.safe_addstr(win, y, x, "3. Press 4 to watch AI thinking")
        y += 1
        self.safe_addstr(win, y, x, "4. Press 5 to view logs")

    def handle_key(self, key: int) -> bool:
        """Home panel doesn't handle keys directly."""
        return False
