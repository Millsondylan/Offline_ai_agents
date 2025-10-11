"""AI thinking panel."""

import curses

from agent_dashboard.panels.base import BasePanel


class ThinkingPanel(BasePanel):
    """AI thinking/reasoning panel."""

    def __init__(self, agent_manager, theme_manager):
        super().__init__("AI Thinking", agent_manager, theme_manager)
        self.auto_scroll = True

    def render(self, win, start_y: int, start_x: int, height: int, width: int):
        """Render thought stream."""
        thoughts = self.agent_manager.get_thoughts()

        y = start_y + 1
        x = start_x + 2

        if not thoughts:
            self.safe_addstr(win, y, x, "Waiting for agent thoughts...",
                           self.theme_manager.get('info'))
            return

        # Auto-scroll to bottom if enabled
        max_visible = height - 3
        if self.auto_scroll and len(thoughts) > max_visible:
            self.scroll_offset = len(thoughts) - max_visible

        # Render thoughts
        visible_thoughts = list(thoughts)[self.scroll_offset:]

        for i, thought in enumerate(visible_thoughts):
            if y >= start_y + height - 2:
                break

            time_str = thought.timestamp.strftime("%H:%M:%S")
            text = f"[Cycle {thought.cycle:3}|{time_str}] {thought.content}"

            self.safe_addstr(win, y, x, text[:width-4],
                           self.theme_manager.get('info'))
            y += 1

        # Scroll indicator
        status_y = start_y + height - 1
        if self.auto_scroll:
            self.safe_addstr(win, status_y, x, "[LIVE - Auto-scrolling]",
                           self.theme_manager.get('running'))
        else:
            self.safe_addstr(win, status_y, x, "[PAUSED - Manual scroll]",
                           self.theme_manager.get('warning'))

    def handle_key(self, key: int) -> bool:
        """Handle thinking panel keys."""
        thoughts = self.agent_manager.get_thoughts()

        if key == curses.KEY_UP:
            self.auto_scroll = False
            self.scroll_offset = max(0, self.scroll_offset - 1)
            return True

        elif key == curses.KEY_DOWN:
            self.scroll_offset = min(len(thoughts) - 1, self.scroll_offset + 1)
            return True

        elif key == curses.KEY_HOME:
            self.auto_scroll = False
            self.scroll_offset = 0
            return True

        elif key == curses.KEY_END:
            self.auto_scroll = True
            self.scroll_offset = max(0, len(thoughts) - 10)
            return True

        return False
