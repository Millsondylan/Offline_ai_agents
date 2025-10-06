from __future__ import annotations

from datetime import datetime

from agent_cli.models import AgentStatus
from agent_cli.panels.home import HomePanel


def _status(state: str, *, cycle: int = 1, task: str = "", progress: float = 0.0, message: str = "Idle") -> AgentStatus:
    return AgentStatus(
        lifecycle_state=state,
        cycle=cycle,
        active_task=task,
        progress=progress,
        message=message,
        is_connected=True,
        updated_at=datetime.now(),
    )


def test_home_panel_renders_basics(fake_screen, theme_manager):
    panel = HomePanel()
    panel.render(fake_screen, theme_manager)
    lines = "\n".join(fake_screen.rendered_lines())
    assert "No active agent session" in lines


def test_home_panel_updates_metrics(fake_screen, theme_manager):
    panel = HomePanel()
    panel.update_overview(
        status=_status("running", cycle=42, task="Implement panel", progress=0.5, message="Working"),
        total_tasks=10,
        completed_tasks=4,
        log_entries=25,
    )
    panel.render(fake_screen, theme_manager)
    lines = "\n".join(fake_screen.rendered_lines())
    assert "Cycle 42" in lines
    assert "Active Task: Implement panel" in lines
    assert "Tasks: 4 / 10" in lines
    assert "Logs: 25" in lines
