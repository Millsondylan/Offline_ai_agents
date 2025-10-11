"""Home panel showing high level agent status."""

from __future__ import annotations

from ..models import AgentStatus
from .base import Panel, safe_addstr


class HomePanel(Panel):
    """Displays overall status, metrics and quick hints."""

    footer_hint = "←/→ switch panels | Space pause/resume | ESC back"

    def __init__(self) -> None:
        super().__init__(panel_id="home", title="Home")
        self.status: AgentStatus | None = None
        self.total_tasks = 0
        self.completed_tasks = 0
        self.log_entries = 0

    def update_overview(
        self,
        *,
        status: AgentStatus,
        total_tasks: int,
        completed_tasks: int,
        log_entries: int,
    ) -> None:
        self.status = status
        self.total_tasks = total_tasks
        self.completed_tasks = completed_tasks
        self.log_entries = log_entries

    def render(self, screen, theme) -> None:
        safe_addstr(screen, 0, 0, "Agent Control Panel — Overview", theme.get("highlight"))
        if not self.status:
            safe_addstr(screen, 2, 0, "No active agent session. Press 2 to start the agent.")
            return

        status = self.status
        safe_addstr(screen, 2, 0, f"Status: {status.display_state}")
        safe_addstr(screen, 3, 0, f"Cycle {status.cycle}")
        safe_addstr(screen, 4, 0, f"Active Task: {status.active_task or 'None'}")
        safe_addstr(screen, 5, 0, f"Progress: {status.progress_percent}%")
        safe_addstr(screen, 6, 0, f"Message: {status.message}")
        safe_addstr(
            screen,
            7,
            0,
            f"Tasks: {self.completed_tasks} / {self.total_tasks}",
        )
        safe_addstr(screen, 8, 0, f"Logs: {self.log_entries}")
        safe_addstr(
            screen,
            9,
            0,
            f"Last Updated: {status.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        )

