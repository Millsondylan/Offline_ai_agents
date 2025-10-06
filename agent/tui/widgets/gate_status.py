from __future__ import annotations

from typing import List

from textual.containers import Vertical
from textual.widgets import Label, Static

from ..navigation import NavEntry, NavigationItem
from ..state_watcher import GateState

_GATE_ICONS = {
    "passed": "✓",
    "ok": "✓",
    "allow": "✓",
    "failed": "✗",
    "blocked": "✗",
    "error": "⚠",
    "running": "⟳",
    "pending": "⏳",
}


class GateButton(NavigationItem):
    def __init__(self, name: str, label: str, status: str, index: int) -> None:
        self.gate_name = name
        super().__init__(label, "View gate findings", id=f"gate-{index}")

    def handle_enter(self) -> None:  # type: ignore[override]
        getattr(self.app, "select_gate", lambda _name: None)(self.gate_name)


class GateStatusPanel(Static):
    def __init__(self) -> None:
        super().__init__(id="gate-panel")
        self.title = Label("Gates & Safety", id="gate-title")
        self.gates_container = Vertical(id="gates-container")
        self._nav_entries: List[NavEntry] = []
        self._empty_label: Label | None = None

    def compose(self):
        yield Vertical(
            self.title,
            self.gates_container,
            id="gate-body",
        )

    def update_gates(self, gates: List[GateState]) -> None:
        existing = list(self.gates_container.children)
        for child in existing:
            child.remove()
        self._nav_entries = []
        if not gates:
            if self._empty_label is None:
                self._empty_label = Label("No gates yet", classes="dim")
            if self._empty_label not in self.gates_container.children:
                self.gates_container.mount(self._empty_label)
            self.refresh()
            return
        if self._empty_label is not None and self._empty_label in self.gates_container.children:
            self._empty_label.remove()
        for index, gate in enumerate(gates):
            icon = _GATE_ICONS.get(gate.status.lower(), "⏳")
            label = f"{icon} {gate.name}"
            button = GateButton(gate.name, label, gate.status, index)
            button.enter_action = f"View {gate.name} findings"
            self.gates_container.mount(button)
            self._nav_entries.append(NavEntry(widget_id=button.id or f"gate-{index}", action=button.enter_action))
        self.refresh()

    def nav_entries(self) -> List[NavEntry]:
        return list(self._nav_entries)
