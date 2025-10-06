from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import Label, Static

from ..state_watcher import CycleState


class CycleInfoPanel(Static):
    def __init__(self) -> None:
        super().__init__(id="cycle-info")
        self.title = Label("═══ CYCLE INFO ═══", classes="panel-title")
        self.cycle_label = Label("Cycle: --", id="cycle-number")
        self.phase_label = Label("Phase: waiting", id="cycle-phase")
        self.timer_label = Label("Elapsed: 0s | ETA: --", id="cycle-timer")
        self.fastpath_label = Label("Fastpath: --", id="cycle-fastpath")

    def compose(self):
        yield Vertical(
            self.title,
            self.cycle_label,
            self.phase_label,
            self.timer_label,
            self.fastpath_label,
            id="cycle-body",
        )

    def update_state(self, state: CycleState) -> None:
        self.cycle_label.update(f"Cycle: {state.cycle_number}")
        self.phase_label.update(f"Phase: {state.phase}")
        self.timer_label.update(f"Elapsed: {state.elapsed} | ETA: {state.estimate}")
        self.fastpath_label.update(f"Fastpath: {state.fastpath}")
