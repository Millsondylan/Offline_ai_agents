"""Navigation utilities for the lightweight TUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class NavEntry:
    """Represents a focusable widget in the navigation order."""

    widget_id: str
    label: str


class NavigationManager:
    """Manages focus movement between navigation entries."""

    def __init__(self, app) -> None:
        self.app = app
        self.entries: List[NavEntry] = []
        self.current_index = 0

    def set_entries(self, entries: List[NavEntry]) -> None:
        """Replace the navigation entries, preserving focus when possible."""
        previous_id: Optional[str] = None
        if self.entries and 0 <= self.current_index < len(self.entries):
            previous_id = self.entries[self.current_index].widget_id

        self.entries = list(entries)
        if not self.entries:
            self.current_index = 0
            return

        if previous_id:
            for idx, entry in enumerate(self.entries):
                if entry.widget_id == previous_id:
                    self.current_index = idx
                    break
            else:
                self.current_index = 0
        else:
            self.current_index = min(self.current_index, len(self.entries) - 1)

    def get_focused(self) -> NavEntry:
        if not self.entries:
            raise IndexError("Navigation list is empty")
        return self.entries[self.current_index]

    def focus_next(self) -> None:
        if not self.entries:
            return
        self.current_index = (self.current_index + 1) % len(self.entries)

    def focus_previous(self) -> None:
        if not self.entries:
            return
        self.current_index = (self.current_index - 1) % len(self.entries)

