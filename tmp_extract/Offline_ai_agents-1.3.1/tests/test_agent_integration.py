from __future__ import annotations

import asyncio
from datetime import datetime

import pytest
from agent_cli.agent_controller import AgentController
from agent_cli.models import AgentStatus, LogEntry, Thought


@pytest.mark.asyncio
async def test_status_subscription_receives_updates_within_100ms(tmp_path):
    controller = AgentController(control_dir=tmp_path)
    updates = []

    controller.subscribe_status(lambda status: updates.append(status))

    await controller.start()
    status = AgentStatus(
        lifecycle_state="running",
        cycle=42,
        active_task="Implement feature",
        progress=0.2,
        message="Working",
        is_connected=True,
        updated_at=datetime.now(),
    )

    await controller.publish_status(status)
    received = await asyncio.wait_for(controller.status_queue.get(), timeout=0.1)

    assert received.cycle == 42
    assert updates[-1].cycle == 42
    assert controller.status.lifecycle_state == "running"


@pytest.mark.asyncio
async def test_pause_resume_issue_commands_and_update_status(tmp_path):
    controller = AgentController(control_dir=tmp_path)
    await controller.start()

    await controller.pause()
    pause_cmd = tmp_path / "pause.cmd"
    assert pause_cmd.exists()
    assert controller.status.lifecycle_state == "paused"

    await controller.resume()
    resume_cmd = tmp_path / "resume.cmd"
    assert resume_cmd.exists()
    assert controller.status.lifecycle_state == "running"


@pytest.mark.asyncio
async def test_stop_transitions_to_stopped_state(tmp_path):
    controller = AgentController(control_dir=tmp_path)
    await controller.start()
    await controller.stop()

    stop_cmd = tmp_path / "stop.cmd"
    assert stop_cmd.exists()
    assert controller.status.lifecycle_state == "stopped"


@pytest.mark.asyncio
async def test_agent_exception_sets_error_state(tmp_path):
    controller = AgentController(control_dir=tmp_path)
    await controller.start()

    await controller.handle_agent_exception(RuntimeError("boom"))
    latest = await asyncio.wait_for(controller.status_queue.get(), timeout=0.1)

    assert latest.lifecycle_state == "error"
    assert "boom" in controller.last_error_message


@pytest.mark.asyncio
async def test_thought_and_log_queues_receive_events(tmp_path):
    controller = AgentController(control_dir=tmp_path)
    await controller.start()

    thought = Thought(
        cycle=5,
        timestamp=datetime.now(),
        content="Considering options",
        thought_type="reasoning",
    )
    log = LogEntry(
        cycle=5,
        timestamp=datetime.now(),
        level="INFO",
        message="Running diagnostics",
    )

    await controller.publish_thought(thought)
    await controller.publish_log(log)

    thought_received = await asyncio.wait_for(controller.thought_queue.get(), timeout=0.1)
    log_received = await asyncio.wait_for(controller.log_queue.get(), timeout=0.1)

    assert thought_received == thought
    assert log_received == log


@pytest.mark.asyncio
async def test_connection_loss_marks_status_disconnected(tmp_path):
    controller = AgentController(control_dir=tmp_path)
    await controller.start()

    await controller.mark_disconnected("network timeout")
    latest = await asyncio.wait_for(controller.status_queue.get(), timeout=0.1)

    assert latest.is_connected is False
    assert controller.status.message.startswith("Disconnected")

    await controller.mark_reconnected()
    latest = await asyncio.wait_for(controller.status_queue.get(), timeout=0.1)
    assert latest.is_connected is True
