"""Verification details dashboard panel."""

from agent_dashboard.panels.base import BasePanel


class VerificationDetailsPanel(BasePanel):
    """Verification details dashboard panel."""

    def __init__(self, agent_manager, theme_manager, check):
        super().__init__("Verification Details", agent_manager, theme_manager)
        self.check = check

    def render(self, win, start_y: int, start_x: int, height: int, width: int):
        """Render verification details dashboard."""
        y = start_y + 2
        x = start_x + 2

        self.safe_addstr(win, y, x, f"Check: {self.check['name']}", self.theme_manager.get('highlight'))
        y += 2

        self.safe_addstr(win, y, x, f"ID: {self.check['id']}")
        y += 1
        self.safe_addstr(win, y, x, f"Description: {self.check['description']}")
        y += 1
        self.safe_addstr(win, y, x, f"Level: {self.check['level']}")
        y += 1
        self.safe_addstr(win, y, x, f"Required: {self.check['required']}")
        y += 1
        self.safe_addstr(win, y, x, f"Enabled: {self.check['enabled']}")
        y += 2

        if self.check.get('result'):
            result = self.check['result']
            self.safe_addstr(win, y, x, "Last Result:", self.theme_manager.get('highlight'))
            y += 1
            self.safe_addstr(win, y, x, f"  Passed: {result['passed']}")
            y += 1
            self.safe_addstr(win, y, x, f"  Message: {result['message']}")
            y += 1
            self.safe_addstr(win, y, x, f"  Timestamp: {result['timestamp']}")

    def handle_key(self, key: int) -> bool:
        """Handle key input for verification details panel."""
        return False
