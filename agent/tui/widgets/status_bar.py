from __future__ import annotations

from textual.containers import Horizontal
from textual.widgets import Label, Static


class StatusBar(Static):
    def __init__(self) -> None:
        super().__init__(id="status-bar")
        self.instructions = Label("1-9,0=jump • ↑↓jk=move • ENTER/SPC=select • q/ESC=quit • h=help", id="status-help")
        self.focused_action = Label("Ready", id="status-action")

    def compose(self):
        yield Horizontal(self.instructions, self.focused_action, id="status-container")

    def update_action(self, text: str | None) -> None:
        self.focused_action.update(text or "Ready")
