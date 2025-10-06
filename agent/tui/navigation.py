from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

from textual import events
from textual.app import App
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button


@dataclass
class NavEntry:
    """Represents a focusable element in the global navigation chain."""

    widget_id: str
    action: str


class NavigationHint(Message):
    """Posted by widgets when the focus changes to update the status bar."""

    def __init__(self, widget: "NavigationItem") -> None:
        super().__init__()
        self.widget = widget
        self.action = widget.enter_action


class NavigationItem(Button):
    """Base button with arrow-navigation styling and focus indication."""

    def __init__(
        self,
        label: str,
        action: str,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(label=label, id=id, classes=classes)
        self.enter_action = action
        self._base_label = label
        self._focused = False
        self._render_label()

    def set_display(self, label: str) -> None:
        self._base_label = label
        self._render_label()

    def handle_enter(self) -> None:
        """Default ENTER handler simply presses the button."""
        self.press()

    def on_focus(self, event: events.Focus) -> None:  # type: ignore[override]
        super().on_focus(event)
        self._focused = True
        self._render_label()
        self.post_message(NavigationHint(self))

    def on_blur(self, event: events.Blur) -> None:  # type: ignore[override]
        super().on_blur(event)
        self._focused = False
        self._render_label()

    def _render_label(self) -> None:
        prefix = "►" if self._focused else " "
        self.label = f"{prefix} {self._base_label}"


class NavigationManager:
    """Maintains deterministic UP/DOWN focus order across the entire UI."""

    def __init__(
        self,
        app: App,
        *,
        on_focus_change: Optional[Callable[[Optional[NavEntry]], None]] = None,
    ) -> None:
        self._app = app
        self._entries: List[NavEntry] = []
        self._index: int = 0
        self._on_focus_change = on_focus_change

    def set_entries(self, entries: Sequence[NavEntry]) -> None:
        filtered: List[NavEntry] = []
        for entry in entries:
            if self._resolve_widget(entry.widget_id) is not None:
                filtered.append(entry)
        self._entries = filtered
        if not self._entries:
            self._notify_focus(None)
            return
        current_id = self._current_focus_id()
        existing = self._index_of(current_id) if current_id else None
        if existing is None:
            self._index = max(0, min(self._index, len(self._entries) - 1))
            self.focus_index(self._index)
        else:
            self._index = existing
            self._notify_focus(self._entries[self._index])

    def focus_next(self) -> None:
        if not self._entries:
            return
        self._index = (self._index + 1) % len(self._entries)
        self.focus_index(self._index)

    def focus_previous(self) -> None:
        if not self._entries:
            return
        self._index = (self._index - 1) % len(self._entries)
        self.focus_index(self._index)

    def focus_index(self, index: int) -> None:
        if not self._entries:
            return
        index %= len(self._entries)
        entry = self._entries[index]
        widget = self._resolve_widget(entry.widget_id)
        if widget is None:
            return
        self._index = index
        self._app.set_focus(widget)
        self._notify_focus(entry)

    def activate_focused(self) -> None:
        widget = self._app.focused
        if widget is None:
            return
        if hasattr(widget, "handle_enter"):
            getattr(widget, "handle_enter")()  # type: ignore[misc]
        elif hasattr(widget, "press"):
            widget.press()  # type: ignore[attr-defined]

    def _current_focus_id(self) -> Optional[str]:
        focused = self._app.focused
        if focused is None:
            return None
        return getattr(focused, "id", None)

    def _index_of(self, widget_id: Optional[str]) -> Optional[int]:
        if widget_id is None:
            return None
        for idx, entry in enumerate(self._entries):
            if entry.widget_id == widget_id:
                return idx
        return None

    def _resolve_widget(self, widget_id: str) -> Optional[Widget]:
        for node in self._app.query(f"#{widget_id}"):
            return node
        return None

    def _notify_focus(self, entry: Optional[NavEntry]) -> None:
        if self._on_focus_change is not None:
            self._on_focus_change(entry)


__all__ = [
    "NavEntry",
    "NavigationHint",
    "NavigationItem",
    "NavigationManager",
]
