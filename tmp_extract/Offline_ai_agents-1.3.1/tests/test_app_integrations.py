from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from agent_cli.app import run_agent_listener, run_logs_listener, run_thought_listener
from agent_cli.models import AgentStatus, LogEntry, Thought


def status_updated() -> datetime:
    return datetime.now()


@pytest.mark.asyncio
async def test_agent_listener_updates_ui(stub_agent_controller, fake_screen, theme_manager):
    status = AgentStatus(
        lifecycle_state="running",
        cycle=1,
        active_task="Test",
        progress=0.5,
        message="Working",
        is_connected=True,
        updated_at=status_updated(),
    )
    stub_agent_controller.status_queue = asyncio.Queue()
    await stub_agent_controller.status_queue.put(status)

    ui = MagicMock()
    task = asyncio.create_task(run_agent_listener(stub_agent_controller, ui))
    await asyncio.sleep(0)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    ui.update_status.assert_called_with(status)


@pytest.mark.asyncio
async def test_thought_listener_feeds_panel(fake_screen, theme_manager):
    controller = MagicMock()
    controller.thought_queue = asyncio.Queue()
    thought = Thought(cycle=1, timestamp=status_updated(), content="Hello", thought_type="reasoning")
    await controller.thought_queue.put(thought)
    panel = MagicMock()
    ui = MagicMock()
    task = asyncio.create_task(run_thought_listener(controller, panel, ui))
    await asyncio.sleep(0)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    panel.add_thought.assert_called_with(thought)


@pytest.mark.asyncio
async def test_logs_listener_updates_panel(fake_screen, theme_manager):
    controller = MagicMock()
    controller.log_queue = asyncio.Queue()
    log = LogEntry(cycle=1, timestamp=status_updated(), level="INFO", message="log")
    await controller.log_queue.put(log)
    panel = MagicMock()
    ui = MagicMock()
    task = asyncio.create_task(run_logs_listener(controller, panel, ui))
    await asyncio.sleep(0)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    panel.add_log.assert_called_with(log)
