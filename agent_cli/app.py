"""Async helper tasks that bridge queues to the UI."""

from __future__ import annotations

import asyncio
from typing import Any

from .agent_controller import AgentController
from .models import AgentStatus, LogEntry, Thought


async def _loop_queue(queue: "asyncio.Queue[Any]", handler) -> None:
    try:
        while True:
            item = await queue.get()
            handler(item)
    except asyncio.CancelledError:  # pragma: no cover - cancellation path
        pass


async def run_agent_listener(controller: AgentController, ui_manager) -> None:
    """Pump status updates from the controller into the UI."""

    def on_status(status: AgentStatus) -> None:
        ui_manager.update_status(status)

    await _loop_queue(controller.status_queue, on_status)


async def run_thought_listener(controller: AgentController, panel, ui_manager) -> None:
    """Forward streamed thoughts to the thinking panel."""

    def on_thought(thought: Thought) -> None:
        panel.add_thought(thought)
        ui_manager.render()

    await _loop_queue(controller.thought_queue, on_thought)


async def run_logs_listener(controller: AgentController, panel, ui_manager) -> None:
    """Forward log entries to the logs panel."""

    def on_log(log: LogEntry) -> None:
        panel.add_log(log)
        ui_manager.render()

    await _loop_queue(controller.log_queue, on_log)

