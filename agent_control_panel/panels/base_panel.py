"""Base panel class for all UI panels."""

import curses
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from agent_control_panel.utils.keyboard import MappedKey


logger = logging.getLogger(__name__)


class BasePanel(ABC):
    """Abstract base class for all panels."""

    def __init__(
        self,
        name: str,
        window: Any,
        state_manager: Optional[Any] = None,
    ):
        """Initialize base panel.

        Args:
            name: Panel name/identifier
            window: Curses window for rendering
            state_manager: Optional state manager for persistence
        """
        self.name = name
        self.window = window
        self.state_manager = state_manager
        self.is_active = False
        self.scroll_offset = 0
        self.max_scroll = 0

        # Restore saved state
        if self.state_manager:
            saved_scroll = self.state_manager.get(f"{self.name}.scroll_offset")
            if saved_scroll is not None:
                self.scroll_offset = saved_scroll

    def activate(self) -> None:
        """Activate this panel (give it focus)."""
        self.is_active = True
        logger.debug(f"Panel '{self.name}' activated")

    def deactivate(self) -> None:
        """Deactivate this panel (remove focus)."""
        self.is_active = False
        logger.debug(f"Panel '{self.name}' deactivated")

    def has_focus(self) -> bool:
        """Check if panel currently has focus.

        Returns:
            True if panel is active
        """
        return self.is_active

    def on_key(self, key: MappedKey) -> bool:
        """Handle keyboard input.

        Args:
            key: Mapped keyboard input

        Returns:
            True if key was handled, False otherwise
        """
        return self.handle_key(key)

    @abstractmethod
    def handle_key(self, key: MappedKey) -> bool:
        """Handle keyboard input (to be implemented by subclasses).

        Args:
            key: Mapped keyboard input

        Returns:
            True if key was handled, False otherwise
        """
        pass

    @abstractmethod
    def render(self) -> None:
        """Render the panel (to be implemented by subclasses)."""
        pass

    def save_state(self) -> None:
        """Save panel state to state manager."""
        if self.state_manager:
            self.state_manager.set(f"{self.name}.scroll_offset", self.scroll_offset)

    def scroll_up(self, lines: int = 1) -> None:
        """Scroll content up.

        Args:
            lines: Number of lines to scroll
        """
        self.scroll_offset = max(0, self.scroll_offset - lines)
        self.save_state()

    def scroll_down(self, lines: int = 1) -> None:
        """Scroll content down.

        Args:
            lines: Number of lines to scroll
        """
        self.scroll_offset = min(self.max_scroll, self.scroll_offset + lines)
        self.save_state()

    def scroll_to_top(self) -> None:
        """Scroll to top of content."""
        self.scroll_offset = 0
        self.save_state()

    def scroll_to_bottom(self) -> None:
        """Scroll to bottom of content."""
        self.scroll_offset = self.max_scroll
        self.save_state()

    def _safe_addstr(
        self,
        y: int,
        x: int,
        text: str,
        attr: int = curses.A_NORMAL,
    ) -> None:
        """Safely add string to window, catching boundary errors.

        Args:
            y: Y coordinate
            x: X coordinate
            text: Text to display
            attr: curses attribute
        """
        try:
            max_y, max_x = self.window.getmaxyx()
            if 0 <= y < max_y and 0 <= x < max_x:
                # Truncate text if it exceeds window width
                available_width = max_x - x - 1
                if len(text) > available_width:
                    text = text[:available_width]
                self.window.addstr(y, x, text, attr)
        except curses.error:
            # Ignore errors from writing at boundaries
            logger.debug(f"Curses error writing at ({y}, {x}): {text[:20]}...")

    def _render_title(self, title: str, attr: int = curses.A_BOLD) -> None:
        """Render panel title bar.

        Args:
            title: Title text
            attr: curses attribute for title
        """
        try:
            max_y, max_x = self.window.getmaxyx()
            # Draw title bar
            title_text = f" {title} "
            padding = "─" * (max_x - len(title_text) - 2)
            full_title = f"┌{title_text}{padding}┐"
            self._safe_addstr(0, 0, full_title, attr)
        except Exception as e:
            logger.error(f"Error rendering title: {e}")

    def _clear(self) -> None:
        """Clear the panel window."""
        try:
            self.window.clear()
        except curses.error:
            pass

    def _refresh(self) -> None:
        """Refresh the panel window."""
        try:
            self.window.refresh()
        except curses.error:
            pass

    def pre_render(self) -> None:
        """Prepare for rendering (clear window)."""
        self._clear()

    def post_render(self) -> None:
        """Finalize rendering (refresh window)."""
        self._refresh()

    def full_render(self) -> None:
        """Perform full render cycle."""
        try:
            self.pre_render()
            self.render()
            self.post_render()
        except Exception as e:
            logger.error(f"Error in full render for panel '{self.name}': {e}")
            # Don't crash - show error in panel instead
            try:
                self._clear()
                self._safe_addstr(0, 0, f"Error rendering {self.name}: {str(e)}")
                self._refresh()
            except Exception:
                pass  # Give up gracefully
