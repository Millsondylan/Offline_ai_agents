"""Navigation system for arrow-key-only TUI control."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, List, TYPE_CHECKING

from textual.widgets import Button

if TYPE_CHECKING:
    from textual.app import App
    from textual.widget import Widget


@dataclass
class NavEntry:
    """A focusable element in the navigation chain."""
    widget_id: str
    action: Optional[str] = None  # Description of what ENTER does


class NavigationItem(Button):
    """A focusable button widget that supports navigation and action execution."""

    def __init__(self, label: str, action: str, **kwargs) -> None:
        super().__init__(label, **kwargs)
        self.enter_action = action

    def set_display(self, label: str) -> None:
        """Update button label."""
        self.label = label

    def handle_enter(self) -> None:
        """Execute the action when ENTER is pressed. Override in subclasses."""
        pass

    def on_activate(self) -> None:
        """Called when the button is activated (clicked or ENTER pressed)."""
        self.handle_enter()


class NavigationManager:
    """Manages arrow-key navigation through focusable elements."""

    def __init__(
        self,
        app: App,
        on_focus_change: Optional[Callable[[Optional[NavEntry]], None]] = None
    ):
        self.app = app
        self.entries: List[NavEntry] = []
        self.current_index = 0
        self.on_focus_change = on_focus_change

    def set_entries(self, entries: List[NavEntry]) -> None:
        """Update the navigation chain, preserving focus if possible."""
        # Remember currently focused widget ID
        current_widget_id = None
        if self.entries and 0 <= self.current_index < len(self.entries):
            current_widget_id = self.entries[self.current_index].widget_id

        # Update entries
        self.entries = entries

        # Try to restore focus to same widget ID
        if current_widget_id:
            for i, entry in enumerate(entries):
                if entry.widget_id == current_widget_id:
                    self.current_index = i
                    self._apply_focus()
                    return

        # Widget not found, reset to 0 or clamp to valid range
        if self.current_index >= len(entries):
            self.current_index = max(0, len(entries) - 1)

        self._apply_focus()

    def focus_next(self) -> None:
        """Move focus to next element (wraps to top)."""
        if not self.entries:
            return
        self.current_index = (self.current_index + 1) % len(self.entries)
        self._apply_focus()

    def focus_previous(self) -> None:
        """Move focus to previous element (wraps to bottom)."""
        if not self.entries:
            return
        self.current_index = (self.current_index - 1) % len(self.entries)
        self._apply_focus()

    def get_focused(self) -> Optional[NavEntry]:
        """Get currently focused navigation entry."""
        if not self.entries or self.current_index >= len(self.entries):
            return None
        return self.entries[self.current_index]

    def activate_focused(self) -> None:
        """Execute the action for the currently focused element."""
        entry = self.get_focused()
        if not entry:
            return

        try:
            widget = self.app.query_one(f"#{entry.widget_id}")
            if hasattr(widget, "handle_enter"):
                widget.handle_enter()
            elif hasattr(widget, "press"):
                widget.press()
        except Exception as e:
            # If widget lookup fails, log it
            if hasattr(self.app, "show_status"):
                self.app.show_status(f"Navigation error: {e}")

    def _apply_focus(self) -> None:
        """Apply focus styling to current element."""
        # Remove focus from all
        removed_count = 0
        for entry in self.entries:
            try:
                widget = self.app.query_one(f"#{entry.widget_id}")
                widget.remove_class("focused")
                removed_count += 1
            except Exception:
                pass

        # Add focus to current
        entry = self.get_focused()
        if entry:
            try:
                widget = self.app.query_one(f"#{entry.widget_id}")
                widget.add_class("focused")

                # Force refresh to ensure CSS is applied
                widget.refresh()

                # Scroll to keep focused widget visible
                widget.scroll_visible(animate=False)

                # Debug: confirm focus was applied
                if hasattr(self.app, "show_status"):
                    classes = " ".join(widget.classes)
                    self.app.show_status(
                        f"Focused: {entry.widget_id} [{self.current_index + 1}/{len(self.entries)}] (classes: {classes})"
                    )

                if self.on_focus_change:
                    self.on_focus_change(entry)
            except Exception as e:
                if hasattr(self.app, "show_status"):
                    self.app.show_status(f"Focus error on {entry.widget_id}: {e}")


class NavigationHint:
    """Message posted when navigation hint should be updated."""
    def __init__(self, action: Optional[str]):
        self.action = action
