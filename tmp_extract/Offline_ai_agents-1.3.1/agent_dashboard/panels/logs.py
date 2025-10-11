"""Execution logs panel."""

import curses

from agent_dashboard.core.models import LogLevel
from agent_dashboard.panels.base import BasePanel


class LogsPanel(BasePanel):
    """Execution logs panel."""

    def __init__(self, agent_manager, theme_manager):
        super().__init__("Logs", agent_manager, theme_manager)
        self.filter_errors_only = False

    def render(self, win, start_y: int, start_x: int, height: int, width: int):
        """Render logs."""
        logs = self.agent_manager.get_logs()

        # Filter if needed
        if self.filter_errors_only:
            logs = [log for log in logs if log.level == LogLevel.ERROR]

        y = start_y + 1
        x = start_x + 2

        if not logs:
            self.safe_addstr(win, y, x, "No logs yet...",
                           self.theme_manager.get('info'))
            return

        # Render logs
        visible_logs = list(logs)[self.scroll_offset:]

        for i, log in enumerate(visible_logs):
            if y >= start_y + height - 2:
                break

            time_str = log.timestamp.strftime("%H:%M:%S")
            level_str = log.level.value[:4]

            # Color by level
            if log.level == LogLevel.ERROR:
                attr = self.theme_manager.get('error')
            elif log.level == LogLevel.WARN:
                attr = self.theme_manager.get('warning')
            else:
                attr = self.theme_manager.get('normal')

            text = f"[{time_str}][Cycle {log.cycle:3}][{level_str}] {log.message}"
            self.safe_addstr(win, y, x, text[:width-4], attr)
            y += 1

        # Filter indicator
        if self.filter_errors_only:
            status_y = start_y + height - 1
            self.safe_addstr(win, status_y, x, "[FILTERED: Errors Only]",
                           self.theme_manager.get('warning'))

    def handle_key(self, key: int) -> bool:
        """Handle logs panel keys."""
        logs = self.agent_manager.get_logs()

        if key == curses.KEY_UP:
            self.scroll_offset = max(0, self.scroll_offset - 1)
            return True

        elif key == curses.KEY_DOWN:
            self.scroll_offset = min(len(logs) - 1, self.scroll_offset + 1)
            return True

        elif key in (ord('f'), ord('F')):
            # Toggle filter
            self.filter_errors_only = not self.filter_errors_only
            self.scroll_offset = 0
            return True

        elif key in (ord('c'), ord('C')):
            # Clear logs
            self.agent_manager.logs.clear()
            self.scroll_offset = 0
            return True

        return False
