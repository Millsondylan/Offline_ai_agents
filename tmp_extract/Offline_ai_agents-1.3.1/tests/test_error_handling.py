from __future__ import annotations

import asyncio

import pytest
from agent_cli.agent_controller import AgentController
from agent_cli.panels.home import HomePanel
from agent_cli.panels.logs import LogsPanel
from agent_cli.panels.task_manager import TaskManagerPanel
from agent_cli.state_manager import StateManager
from agent_cli.ui_manager import UIManager


@pytest.mark.asyncio
async def test_agent_controller_crash_preserves_queue(tmp_path):
    controller = AgentController(control_dir=tmp_path)
    await controller.start()
    await controller.handle_agent_exception(RuntimeError("failure"))
    latest = await asyncio.wait_for(controller.status_queue.get(), timeout=0.1)
    assert latest.lifecycle_state == "error"
    assert controller.status.lifecycle_state == "error"
    assert "failure" in controller.last_error_message


def test_task_manager_gracefully_handles_corrupt_file(tmp_path, stub_interaction):
    storage = tmp_path / "tasks.json"
    storage.write_text("not json")
    panel = TaskManagerPanel(storage_path=storage, interaction=stub_interaction)
    assert panel.tasks == []


def test_logs_panel_search_without_matches(tmp_path, stub_interaction):
    panel = LogsPanel(log_dir=tmp_path, interaction=stub_interaction)
    stub_interaction.queue_prompt("missing")
    handled = panel.handle_key(ord("/"))
    assert handled is True
    assert panel.search_matches == []
    assert panel.handle_key(ord("n")) is False


def test_ui_manager_renders_resize_warning(theme_manager, stub_agent_controller):
    from tests.conftest import FakeScreen

    small_screen = FakeScreen(height=10, width=40)
    state_manager = StateManager(base_path=None)
    manager = UIManager(
        screen=small_screen,
        agent_controller=stub_agent_controller,
        panels=[HomePanel()],
        theme_manager=theme_manager,
        state_manager=state_manager,
    )
    manager.render()
    rendered = "\n".join(small_screen.rendered_lines())
    assert "Terminal too small" in rendered
