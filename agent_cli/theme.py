"""Minimal theme management for the compatibility UI."""

from __future__ import annotations

import curses
from typing import Dict


class ThemeManager:
    """Tracks foreground/background attribute pairs for a small palette."""

    _DEFAULTS: Dict[str, Dict[str, int]] = {
        "dark": {
            "header": curses.A_BOLD,
            "highlight": curses.A_BOLD,
            "selected": curses.A_REVERSE,
            "normal": curses.A_NORMAL,
            "warning": curses.A_BOLD,
        },
        "light": {
            "header": curses.A_BOLD,
            "highlight": curses.A_BOLD,
            "selected": curses.A_REVERSE,
            "normal": curses.A_NORMAL,
            "warning": curses.A_BOLD,
        },
    }

    def __init__(self) -> None:
        self.active_theme = "dark"
        self._palette = ThemeManager._DEFAULTS.copy()
        self.initialised = False

    def initialize(self) -> None:
        """Marks curses colour initialisation as performed."""
        self.initialised = True

    def toggle(self) -> None:
        """Flip between dark and light palettes."""
        self.active_theme = "light" if self.active_theme == "dark" else "dark"

    def set_theme(self, theme: str) -> None:
        if theme in self._palette:
            self.active_theme = theme

    def get(self, role: str) -> int:
        """Return curses attribute for a semantic role."""
        return self._palette[self.active_theme].get(role, curses.A_NORMAL)

