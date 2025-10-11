"""Theme management for dark/light mode."""

import curses
from enum import Enum


class Theme(str, Enum):
    """Available themes."""
    DARK = "dark"
    LIGHT = "light"


class ThemeManager:
    """Manages UI themes and colors."""

    def __init__(self):
        self.current_theme = Theme.DARK
        self.color_pairs = {}

    def initialize(self):
        """Initialize curses colors."""
        try:
            if not curses.has_colors():
                self._init_fallback_colors()
                return

            curses.start_color()
            curses.use_default_colors()

            if self.current_theme == Theme.DARK:
                self._init_dark_theme()
            else:
                self._init_light_theme()
        except curses.error:
            # Fallback if curses is not properly initialized
            self._init_fallback_colors()

    def _init_dark_theme(self):
        """Initialize dark theme colors."""
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Normal
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)    # Header
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Success/Running
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)      # Error/Stopped
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # Warning/Paused
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)     # Info
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)     # Selected
        curses.init_pair(8, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Highlight

        self.color_pairs = {
            'normal': curses.color_pair(1),
            'header': curses.color_pair(2),
            'running': curses.color_pair(3),
            'error': curses.color_pair(4),
            'warning': curses.color_pair(5),
            'info': curses.color_pair(6),
            'selected': curses.color_pair(7),
            'highlight': curses.color_pair(8),
        }

    def _init_light_theme(self):
        """Initialize light theme colors."""
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)    # Normal
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Header
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_WHITE)    # Success
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_WHITE)      # Error
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_WHITE)   # Warning
        curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_WHITE)     # Info
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN)     # Selected
        curses.init_pair(8, curses.COLOR_MAGENTA, curses.COLOR_WHITE)  # Highlight

        self.color_pairs = {
            'normal': curses.color_pair(1),
            'header': curses.color_pair(2),
            'running': curses.color_pair(3),
            'error': curses.color_pair(4),
            'warning': curses.color_pair(5),
            'info': curses.color_pair(6),
            'selected': curses.color_pair(7),
            'highlight': curses.color_pair(8),
        }

    def _init_fallback_colors(self):
        """Initialize fallback colors when curses is not available."""
        self.color_pairs = {
            'normal': 0,
            'header': 0,
            'running': 0,
            'error': 0,
            'warning': 0,
            'info': 0,
            'selected': 0,
            'highlight': 0,
        }

    def toggle(self):
        """Toggle between dark and light theme."""
        self.current_theme = Theme.LIGHT if self.current_theme == Theme.DARK else Theme.DARK
        self.initialize()

    def get(self, color_name: str) -> int:
        """Get color pair by name."""
        return self.color_pairs.get(color_name, curses.color_pair(0))
