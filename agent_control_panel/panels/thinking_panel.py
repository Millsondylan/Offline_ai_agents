"""Thinking stream panel."""

import curses
from collections import deque
from agent_control_panel.panels.base_panel import BasePanel
from agent_control_panel.utils.keyboard import Key, MappedKey


class ThinkingPanel(BasePanel):
    """Panel for displaying agent thoughts."""

    def __init__(self, window, agent_controller, state_manager=None):
        super().__init__("Thinking", window, state_manager)
        self.agent_controller = agent_controller
        self.thoughts = deque(maxlen=1000)
        self.auto_scroll = True

        # Subscribe to thoughts
        agent_controller.subscribe_thoughts(self._on_thought)

    def _on_thought(self, thought):
        """Handle new thought."""
        self.thoughts.append(thought)
        if self.auto_scroll:
            self.scroll_offset = max(0, len(self.thoughts) - 10)

    def handle_key(self, key: MappedKey) -> bool:
        """Handle keyboard input."""
        if key == Key.UP:
            self.auto_scroll = False
            self.scroll_up()
            return True
        elif key == Key.DOWN:
            self.scroll_down()
            return True
        elif key == Key.END:
            self.auto_scroll = True
            self.scroll_to_bottom()
            return True
        elif key == Key.HOME:
            self.auto_scroll = False
            self.scroll_to_top()
            return True
        return False

    def render(self) -> None:
        """Render thoughts."""
        self._render_title("AI Thinking (Live)")

        if not self.thoughts:
            self._safe_addstr(2, 2, "Waiting for agent thoughts...")
            return

        max_y, max_x = self.window.getmaxyx()
        display_height = max_y - 3

        thoughts_list = list(self.thoughts)
        start_idx = self.scroll_offset
        end_idx = min(start_idx + display_height, len(thoughts_list))

        y = 2
        for thought in thoughts_list[start_idx:end_idx]:
            time_str = thought.timestamp.strftime("%H:%M:%S")
            text = f"[Cycle {thought.cycle}|{time_str}] {thought.content}"
            self._safe_addstr(y, 2, text[:max_x-4])
            y += 1

        # Show scroll indicator
        if not self.auto_scroll:
            self._safe_addstr(max_y-1, 2, "[MANUAL SCROLL]", curses.A_BOLD)
        else:
            self._safe_addstr(max_y-1, 2, "[LIVE]", curses.A_BOLD)
