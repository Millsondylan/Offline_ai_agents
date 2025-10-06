"""Home dashboard panel."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from agent_cli.models import AgentStatus
from agent_cli.panels.base import Panel
from agent_cli.theme import ThemeManager


@dataclass
class DashboardMetrics:
    total_tasks: int = 0
    completed_tasks: int = 0
    log_entries: int = 0


class HomePanel(Panel):
    """Provide a high-level overview of agent activity."""

    def __init__(self) -> None:
        super().__init__(panel_id="home", title="Home")
        self.status: Optional[AgentStatus] = None
        self.metrics = DashboardMetrics()
        self._last_message: str = "No active agent session"

    def update_overview(
        self,
        *,
        status: AgentStatus,
        total_tasks: int,
        completed_tasks: int,
        log_entries: int,
    ) -> None:
        self.status = status
        self.metrics = DashboardMetrics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            log_entries=log_entries,
        )
        self._last_message = status.message
        self.mark_dirty()

    def render(self, screen, theme: ThemeManager) -> None:  # type: ignore[override]
        screen.addstr(3, 2, "Agent Overview")
        screen.addstr(4, 2, "──────────────────────────────────────────────────────────────────")
        if self.status is None:
            screen.addstr(6, 2, self._last_message)
            return

        status = self.status
        screen.addstr(6, 2, f"Lifecycle : {status.status_display()}")
        screen.addstr(7, 2, f"Cycle     : {status.cycle}")
        screen.addstr(8, 2, f"Progress  : {status.progress_percent()}%")
        active_task = status.active_task or "None"
        screen.addstr(9, 2, f"Active Task: {active_task}")
        screen.addstr(10, 2, f"Message   : {status.message}")
        screen.addstr(12, 2, f"Tasks: {self.metrics.completed_tasks} / {self.metrics.total_tasks}")
        screen.addstr(13, 2, f"Logs : {self.metrics.log_entries}")

    def footer(self) -> str:
        return "Use 1-9 keys to navigate sections"

    def capture_state(self) -> dict:
        if self.status is None:
            return {}
        return {
            "status": {
                "lifecycle_state": self.status.lifecycle_state,
                "cycle": self.status.cycle,
                "active_task": self.status.active_task,
                "progress": self.status.progress,
                "message": self.status.message,
                "is_connected": self.status.is_connected,
                "updated_at": self.status.updated_at.isoformat(),
            },
            "metrics": {
                "total_tasks": self.metrics.total_tasks,
                "completed_tasks": self.metrics.completed_tasks,
                "log_entries": self.metrics.log_entries,
            },
        }

    def restore_state(self, state: dict) -> None:
        status_data = state.get("status")
        if status_data:
            updated_at_raw = status_data.get("updated_at")
            updated_at = datetime.fromisoformat(updated_at_raw) if updated_at_raw else datetime.now()
            self.status = AgentStatus(
                lifecycle_state=status_data["lifecycle_state"],
                cycle=status_data["cycle"],
                active_task=status_data["active_task"],
                progress=status_data["progress"],
                message=status_data["message"],
                is_connected=status_data["is_connected"],
                updated_at=updated_at,
            )
            self._last_message = self.status.message
        metrics_data = state.get("metrics")
        if metrics_data:
            self.metrics = DashboardMetrics(
                total_tasks=metrics_data.get("total_tasks", 0),
                completed_tasks=metrics_data.get("completed_tasks", 0),
                log_entries=metrics_data.get("log_entries", 0),
            )
        self.mark_dirty()


__all__ = ["HomePanel"]
