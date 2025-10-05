from __future__ import annotations

from typing import Optional

try:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import Footer, Header, Static, Input
except Exception as e:  # pragma: no cover - runtime
    App = object  # type: ignore
    ComposeResult = object  # type: ignore
    Horizontal = Vertical = object  # type: ignore
    Footer = Header = Static = Input = object  # type: ignore


class AgentApp(App):
    CSS = ""
    TITLE = "Agent"

    def __init__(self) -> None:
        super().__init__()
        self._status: str = "idle"

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Header()
        yield Horizontal(
            Vertical(Static("Tasks\n- Analyze\n- Fix Style\n- Fix Security\n- Run Tests\n- Enhance Codebase"), id="left"),
            Vertical(Static("Thinking & Actions\n(Logs will appear here)\nUse /start to run headless cycle."), id="center"),
            Vertical(Static("Panels: Diff | Findings | Models | Config | Artifacts"), id="right"),
        )
        yield Footer()

    def on_mount(self) -> None:  # type: ignore[override]
        self.query_one(Static).update("Ready. Press S to Start/Stop. D=Diff F=Fix G=Gate M=Models P=Push")

    def action_start(self) -> None:
        self._status = "running"
        self._log("Started")

    def action_stop(self) -> None:
        self._status = "stopped"
        self._log("Stopped")

    def _log(self, text: str) -> None:
        # Minimal: append to center static
        try:
            center: Static = self.query('#center Static').first()  # type: ignore[attr-defined]
            center.update((center.renderable or "") + f"\n{text}")
        except Exception:
            pass

