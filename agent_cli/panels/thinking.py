"""Thinking panel for streaming agent reasoning."""

from __future__ import annotations

from collections import deque
from typing import Deque, List, Sequence

from agent_cli.models import Thought
from agent_cli.panels.base import Panel
from agent_cli.theme import ThemeManager

KEY_UP = 259
KEY_DOWN = 258
KEY_END = 360


class ThinkingPanel(Panel):
    """Render live agent thoughts with scrollback."""

    def __init__(self, *, max_thoughts: int = 1000) -> None:
        super().__init__(panel_id="thinking", title="AI Thinking")
        self.thoughts: Deque[Thought] = deque(maxlen=max_thoughts)
        self.max_thoughts = max_thoughts
        self.scroll_offset = 0
        self.auto_scroll = True
        self._is_live = True

    def add_thought(self, thought: Thought) -> None:
        self.thoughts.append(thought)
        if self.auto_scroll:
            self.scroll_offset = 0
        else:
            self.scroll_offset = min(self.scroll_offset, max(0, len(self.thoughts) - 1))
        if self.auto_scroll and self._is_live:
            self.scroll_offset = 0
        self.mark_dirty()

    def handle_key(self, key: int) -> bool:
        if key == KEY_UP:
            if len(self.thoughts) <= 1:
                return False
            max_offset = max(0, len(self.thoughts) - 1)
            if self.scroll_offset >= max_offset:
                return False
            self.scroll_offset = min(max_offset, self.scroll_offset + 1)
            self.auto_scroll = False
            self.mark_dirty()
            return True
        if key == KEY_DOWN:
            if self.scroll_offset == 0:
                return False
            self.scroll_offset = max(0, self.scroll_offset - 1)
            if self.scroll_offset == 0:
                self.auto_scroll = True
            self.mark_dirty()
            return True
        if key == KEY_END:
            if self.scroll_offset == 0 and self.auto_scroll:
                return False
            self.scroll_offset = 0
            self.auto_scroll = True
            self.mark_dirty()
            return True
        return False

    def render(self, screen, theme: ThemeManager) -> None:  # type: ignore[override]
        indicator = "[LIVE]" if self._is_live else "[PAUSED]"
        header = f"AI Thinking (Live) {indicator}"
        screen.addstr(3, 2, header[: 76])
        screen.addstr(4, 2, "──────────────────────────────────────────────────────────────────")

        lines = self._visible_lines(height=14)
        if not lines:
            screen.addstr(6, 2, "No thoughts captured yet.")
        else:
            for idx, line in enumerate(lines):
                screen.addstr(5 + idx, 2, line[: 76])

        if self.auto_scroll:
            hint = "↑/↓ pause scroll | End resume live"
        else:
            hint = "↑/↓ navigate | End resume live"
        screen.addstr(20, 2, hint[: 76])

    def footer(self) -> str:
        return "↑/↓ scroll | End resume live"

    def capture_state(self) -> dict:
        return {
            "scroll_offset": self.scroll_offset,
            "auto_scroll": self.auto_scroll,
            "is_live": self._is_live,
        }

    def restore_state(self, state: dict) -> None:
        self.scroll_offset = int(state.get("scroll_offset", 0))
        self.auto_scroll = bool(state.get("auto_scroll", True))
        self._is_live = bool(state.get("is_live", True))
        self.scroll_offset = max(0, min(self.scroll_offset, max(0, len(self.thoughts) - 1)))
        self.mark_dirty()

    def set_live(self, live: bool) -> None:
        self._is_live = live
        if live:
            self.auto_scroll = True
            self.scroll_offset = 0
        self.mark_dirty()

    # ------------------------------------------------------------------
    def _visible_lines(self, *, height: int) -> List[str]:
        if not self.thoughts:
            return []
        window = []  # type: List[str]
        history: Sequence[Thought] = list(self.thoughts)
        end_index = len(history) - self.scroll_offset
        end_index = max(0, min(len(history), end_index))
        start_index = max(0, end_index - height)
        subset = history[start_index:end_index]
        for thought in subset:
            window.extend(self._format_thought(thought))
        return window[-height:]

    def _format_thought(self, thought: Thought) -> List[str]:
        timestamp = thought.timestamp.strftime("%H:%M:%S")
        prefix = f"[Cycle {thought.cycle:04} | {timestamp}] "
        lines = thought.content.splitlines() or [""]
        formatted: List[str] = []
        formatted.append(prefix + lines[0])
        indent = " " * len(prefix)
        for part in lines[1:]:
            formatted.append(indent + part)
        return formatted


__all__ = ["ThinkingPanel", "KEY_UP", "KEY_DOWN", "KEY_END"]
