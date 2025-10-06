"""Base panel class."""

import curses
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_dashboard.core.agent_manager import AgentManager
    from agent_dashboard.core.theme import ThemeManager


class BasePanel(ABC):
    """Base class for all panels."""

    def __init__(self, name: str, agent_manager: 'AgentManager', theme_manager: 'ThemeManager'):
        self.name = name
        self.agent_manager = agent_manager
        self.theme_manager = theme_manager
        self.scroll_offset = 0
        self.selected_index = 0

    @abstractmethod
    def render(self, win, start_y: int, start_x: int, height: int, width: int):
        """Render the panel content."""
        pass

    @abstractmethod
    def handle_key(self, key: int) -> bool:
        """Handle key press. Return True if handled."""
        pass

    def safe_addstr(self, win, y: int, x: int, text: str, attr=0):
        """Safely add string to window."""
        try:
            max_y, max_x = win.getmaxyx()
            if 0 <= y < max_y and 0 <= x < max_x:
                available = max_x - x - 1
                if len(text) > available:
                    text = text[:available]
                win.addstr(y, x, text, attr)
        except curses.error:
            pass
