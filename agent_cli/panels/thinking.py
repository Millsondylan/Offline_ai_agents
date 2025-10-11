"""AI thinking stream panel."""

from __future__ import annotations

import curses
from typing import List

from ..models import Thought
from .base import Panel, safe_addstr

KEY_UP = getattr(curses, "KEY_UP", -1)
KEY_DOWN = getattr(curses, "KEY_DOWN", -2)
KEY_END = getattr(curses, "KEY_END", -5)


class ThinkingPanel(Panel):
    """Displays the rolling window of agent thoughts."""

    footer_hint = "↑/↓ scroll | End resume live | L toggle live"

    def __init__(self, *, max_thoughts: int = 500) -> None:
        super().__init__(panel_id="thinking", title="AI Thinking")
        self.max_thoughts = max_thoughts
        self.thoughts: List[Thought] = []
        self.scroll_offset = 0
        self.auto_scroll = True
        self.is_live = True

    # ------------------------------------------------------------------
    def add_thought(self, thought: Thought) -> None:
        self.thoughts.append(thought)
        if len(self.thoughts) > self.max_thoughts:
            self.thoughts = self.thoughts[-self.max_thoughts :]
        if self.is_live and self.auto_scroll:
            self.scroll_offset = 0

    def set_live(self, live: bool) -> None:
        self.is_live = live
        if live:
            self.auto_scroll = True
            self.scroll_offset = 0

    # ------------------------------------------------------------------
    def handle_key(self, key: int) -> bool:
        if key == KEY_UP:
            if self.thoughts:
                max_offset = max(0, len(self.thoughts) - 1)
                self.scroll_offset = min(self.scroll_offset + 1, max_offset)
                self.auto_scroll = False
            return True
        if key == KEY_DOWN:
            if self.scroll_offset > 0:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            if self.scroll_offset == 0 and self.is_live:
                self.auto_scroll = True
            return True
        if key == KEY_END:
            self.scroll_offset = 0
            self.auto_scroll = True
            return True
        return False

    # ------------------------------------------------------------------
    def _visible_thoughts(self) -> List[Thought]:
        if not self.thoughts:
            return []
        limit = len(self.thoughts) - self.scroll_offset
        return self.thoughts[max(0, limit - 15) : limit]

    def render(self, screen, theme) -> None:
        status = "[LIVE]" if self.is_live else "[PAUSED]"
        safe_addstr(screen, 0, 0, f"AI Thinking Stream {status}")
        if not self.thoughts:
            safe_addstr(screen, 2, 0, "Thought stream empty.")
            return

        for idx, thought in enumerate(self._visible_thoughts()):
            prefix = f"#{thought.cycle:04d} "
            safe_addstr(screen, 2 + idx * 2, 0, prefix + thought.timestamp.strftime("%H:%M:%S"))
            for line_index, line in enumerate(thought.content.splitlines()):
                indent = "    " if line_index else "  "
                safe_addstr(screen, 3 + idx * 2 + line_index, 0, f"{indent}{line}")
