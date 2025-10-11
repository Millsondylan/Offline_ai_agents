"""Base panel scaffolding used by all compatibility panels."""

from __future__ import annotations

import curses
from typing import Any, Dict


def safe_addstr(screen, y: int, x: int, text: str, attr: int | None = None) -> None:
    """Write to a curses screen while ignoring overflow errors."""
    try:
        if attr is None or attr == curses.A_NORMAL:
            screen.addstr(y, x, text)
        else:
            screen.addstr(y, x, text, attr)
    except curses.error:
        # The fake test screen never raises, but real terminals might.
        pass


class Panel:
    """Abstract base class wrapping simple state helpers."""

    footer_hint: str = ""

    def __init__(self, *, panel_id: str, title: str) -> None:
        self.panel_id = panel_id
        self.title = title
        self.state: Dict[str, Any] = {"scroll": 0}

    # ------------------------------------------------------------------
    # Hooks expected by the UI manager
    # ------------------------------------------------------------------
    def render(self, screen, theme) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def handle_key(self, key: int) -> bool:
        if key == ord("j"):
            self.state["scroll"] = self.state.get("scroll", 0) + 1
            return True
        if key == ord("k") and self.state.get("scroll", 0) > 0:
            self.state["scroll"] -= 1
            return True
        return False

    # ------------------------------------------------------------------
    # State capture helpers
    # ------------------------------------------------------------------
    def capture_state(self) -> Dict[str, Any]:
        return dict(self.state)

    def restore_state(self, state: Dict[str, Any]) -> None:
        self.state.update(state)

    def footer(self) -> str:
        return self.footer_hint
