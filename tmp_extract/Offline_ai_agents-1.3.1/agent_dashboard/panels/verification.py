"""Verification dashboard panel."""

import curses

from agent_dashboard.panels.base import BasePanel
from agent_dashboard.panels.verification_details import VerificationDetailsPanel


class VerificationPanel(BasePanel):
    """Verification dashboard panel."""

    def __init__(self, agent_manager, theme_manager, dashboard):
        super().__init__("Verification", agent_manager, theme_manager)
        self.selected_check = 0
        self.dashboard = dashboard

    def render(self, win, start_y: int, start_x: int, height: int, width: int):
        """Render verification dashboard."""
        state = self.agent_manager.get_state()

        y = start_y + 2
        x = start_x + 2

        self.safe_addstr(win, y, x, "Verification Checks", self.theme_manager.get('highlight'))
        y += 2

        if not state.verification_checks:
            self.safe_addstr(win, y, x, "No verification checks configured.")
            return

        for i, check in enumerate(state.verification_checks):
            if y >= start_y + height:
                break

            attr = self.theme_manager.get('selected') if i == self.selected_check else 0

            status = " "
            if check.result:
                status = "✓" if check.result.passed else "✗"

            self.safe_addstr(win, y, x, f"[{status}] {check.name}", attr)
            y += 1

    def handle_key(self, key: int) -> bool:
        """Handle key input for verification panel."""
        if key == ord('r') or key == ord('R'):
            self.agent_manager.run_verification()
            return True
        elif key == curses.KEY_UP:
            self.selected_check = (self.selected_check - 1) % len(self.agent_manager.get_state().verification_checks)
            return True
        elif key == curses.KEY_DOWN:
            self.selected_check = (self.selected_check + 1) % len(self.agent_manager.get_state().verification_checks)
            return True
        elif key in [curses.KEY_ENTER, 10, 13]:
            state = self.agent_manager.get_state()
            if state.verification_checks:
                check = state.verification_checks[self.selected_check]
                details_panel = VerificationDetailsPanel(self.agent_manager, self.theme_manager, check)
                self.dashboard.panels["verification_details"] = details_panel
                self.dashboard.switch_panel("verification_details", "Verification Details")
            return True
        return False
