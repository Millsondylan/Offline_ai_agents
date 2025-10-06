from __future__ import annotations

from typing import List

from textual.containers import Horizontal, Vertical
from textual.widgets import Label, Static

from ..navigation import NavigationItem
from ..state_watcher import ControlState


class PauseResumeButton(NavigationItem):
    def __init__(self) -> None:
        super().__init__("[Pause]", "Pause agent", id="control-pause")
        self._mode = "pause"

    def set_mode(self, mode: str) -> None:
        if mode not in {"pause", "resume"}:
            return
        self._mode = mode
        label = "[Pause]" if mode == "pause" else "[Resume]"
        action = "Pause agent" if mode == "pause" else "Resume agent"
        self.enter_action = action
        self.set_display(label)

    def handle_enter(self) -> None:  # type: ignore[override]
        if self._mode == "pause":
            getattr(self.app, "pause_agent", lambda: None)()
        else:
            getattr(self.app, "resume_agent", lambda: None)()


class StopButton(NavigationItem):
    def __init__(self) -> None:
        super().__init__("[Stop]", "Stop agent", id="control-stop")

    def handle_enter(self) -> None:  # type: ignore[override]
        getattr(self.app, "stop_agent", lambda: None)()


class ModelSwitcherButton(NavigationItem):
    def __init__(self) -> None:
        super().__init__("Model: --", "Switch model", id="control-model")
        self.models: List[str] = []
        self.current: str = "--"

    def update_models(self, models: List[str], current: str) -> None:
        self.models = models or [current] if current else ["--"]
        self.current = current or (self.models[0] if self.models else "--")
        self.set_display(f"Model: {self.current}")
        self.enter_action = "Switch model"

    def handle_enter(self) -> None:  # type: ignore[override]
        if not self.models:
            return
        try:
            idx = self.models.index(self.current)
        except ValueError:
            idx = -1
        next_idx = (idx + 1) % len(self.models)
        self.current = self.models[next_idx]
        self.set_display(f"Model: {self.current}")
        getattr(self.app, "switch_model", lambda _name: None)(self.current)


class ForceCommitButton(NavigationItem):
    def __init__(self) -> None:
        super().__init__("[Force Commit]", "Force commit", id="control-commit")

    def handle_enter(self) -> None:  # type: ignore[override]
        getattr(self.app, "force_commit", lambda: None)()


class ControlPanel(Static):
    def __init__(self) -> None:
        super().__init__(id="control-panel")
        self.status_label = Label("● IDLE", id="status-label")
        self.provider_label = Label("Provider: --", id="provider-label")
        self.session_label = Label("Session: 0s | Cycle: --", id="session-label")
        self.pause_button = PauseResumeButton()
        self.stop_button = StopButton()
        self.model_button = ModelSwitcherButton()
        self.commit_button = ForceCommitButton()

    def compose(self):
        yield Vertical(
            self.status_label,
            self.provider_label,
            self.session_label,
            self.pause_button,
            self.stop_button,
            self.model_button,
            self.commit_button,
            id="control-panel-body",
        )

    def update_state(self, state: ControlState) -> None:
        status = state.status.upper()
        indicator = {
            "RUNNING": "● RUNNING",
            "PAUSED": "⏸ PAUSED",
            "STOPPED": "⏹ STOPPED",
        }.get(status, f"● {status}")
        self.status_label.update(indicator)
        self.provider_label.update(f"Provider: {state.provider} | Model: {state.model}")
        self.session_label.update(
            f"Session: {state.session_duration} | Cycle #{state.cycle_count} ({state.cycle_status})"
        )

        if status == "RUNNING":
            self.pause_button.set_mode("pause")
        else:
            self.pause_button.set_mode("resume")
        self.model_button.update_models(state.available_models, state.model)
