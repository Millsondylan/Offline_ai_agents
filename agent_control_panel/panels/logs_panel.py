"""Logs panel."""

import curses
from collections import deque
from agent_control_panel.core.models import LogLevel
from agent_control_panel.panels.base_panel import BasePanel
from agent_control_panel.utils.keyboard import Key, MappedKey, KeyType


class LogsPanel(BasePanel):
    """Panel for displaying logs."""

    def __init__(self, window, agent_controller, theme_manager, state_manager=None):
        super().__init__("Logs", window, state_manager)
        self.agent_controller = agent_controller
        self.theme_manager = theme_manager
        self.logs = deque(maxlen=5000)
        self.filter_level = None

        # Subscribe to logs
        agent_controller.subscribe_logs(self._on_log)

    def _on_log(self, log):
        """Handle new log entry."""
        self.logs.append(log)

    def handle_key(self, key: MappedKey) -> bool:
        """Handle keyboard input."""
        if key == Key.UP:
            self.scroll_up()
            return True
        elif key == Key.DOWN:
            self.scroll_down()
            return True
        elif key.type == KeyType.CHAR and key.value in ('f', 'F'):
            # Toggle error filter
            self.filter_level = None if self.filter_level else LogLevel.ERROR
            return True
        elif key.type == KeyType.CHAR and key.value in ('c', 'C'):
            self.logs.clear()
            return True
        return False

    def render(self) -> None:
        """Render logs."""
        self._render_title("Execution Logs")

        if not self.logs:
            self._safe_addstr(2, 2, "No logs yet...")
            return

        # Filter logs
        logs_to_show = [
            log for log in self.logs
            if self.filter_level is None or log.level == self.filter_level
        ]

        max_y, max_x = self.window.getmaxyx()
        display_height = max_y - 3

        start_idx = self.scroll_offset
        end_idx = min(start_idx + display_height, len(logs_to_show))

        y = 2
        for log in logs_to_show[start_idx:end_idx]:
            time_str = log.timestamp.strftime("%H:%M:%S")
            level_str = log.level.value.upper()

            # Color based on level
            if log.level == LogLevel.ERROR:
                attr = self.theme_manager.get_color_attr("error")
            elif log.level == LogLevel.WARN:
                attr = self.theme_manager.get_color_attr("warning")
            else:
                attr = self.theme_manager.get_color_attr("info")

            text = f"[{time_str}][{level_str}] {log.message}"
            self._safe_addstr(y, 2, text[:max_x-4], attr)
            y += 1
