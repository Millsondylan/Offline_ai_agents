from __future__ import annotations

from typing import List

from textual.containers import VerticalScroll
from textual.widgets import Label, Static

from ..navigation import NavEntry


class MenuItem(Static):
    """A single menu item showing number and label."""

    def __init__(self, number: int, label: str, item_id: str) -> None:
        super().__init__(id=item_id, classes="menu-item")
        self.number = number
        self.item_label = label

    def render(self) -> str:
        """Render the menu item."""
        display_num = self.number if self.number < 10 else 0
        return f"[{display_num}] {self.item_label}"


class MenuList(Static):
    """Displays all navigable items as a numbered vertical list."""

    def __init__(self) -> None:
        super().__init__(id="menu-list")
        self.title = Label("Options (press number or ↑↓ to select, ENTER to activate)", id="menu-title")
        self.scroll = VerticalScroll(id="menu-scroll")

    def compose(self):
        yield self.title
        yield self.scroll

    def update_items(self, entries: List[NavEntry]) -> None:
        """Update the menu with new items."""
        # Clear existing
        self.scroll.remove_children()

        # Add numbered items
        for i, entry in enumerate(entries):
            display_num = i + 1 if i < 9 else 0
            item = MenuItem(i + 1, entry.action or entry.widget_id, f"menu-item-{i}")
            self.scroll.mount(item)
