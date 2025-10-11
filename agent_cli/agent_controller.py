"""Async controller responsible for issuing commands to the underlying agent."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Callable, List

from .models import AgentStatus, LogEntry, Thought


class AgentController:
    """Small asynchronous façade used by the tests."""

    def __init__(self, *, control_dir: Path) -> None:
        self.control_dir = Path(control_dir)
        self.control_dir.mkdir(parents=True, exist_ok=True)

        self.status = AgentStatus()
        self.status_queue: asyncio.Queue[AgentStatus] = asyncio.Queue()
        self.thought_queue: asyncio.Queue[Thought] = asyncio.Queue()
        self.log_queue: asyncio.Queue[LogEntry] = asyncio.Queue()
        self.status_listeners: List[Callable[[AgentStatus], None]] = []
        self.started = False
        self.last_error_message = ""

    # ------------------------------------------------------------------
    async def start(self) -> None:
        if self.started:
            return
        self.started = True
        self.status.lifecycle_state = "running"
        self.status.message = "Running"
        self.control_dir.mkdir(parents=True, exist_ok=True)

    def subscribe_status(self, callback: Callable[[AgentStatus], None]) -> None:
        self.status_listeners.append(callback)

    async def publish_status(self, status: AgentStatus) -> None:
        self.status = status
        self.status.updated_at = datetime.now()
        for callback in list(self.status_listeners):
            callback(status)
        await self.status_queue.put(status)

    # ------------------------------------------------------------------
    async def pause(self) -> None:
        self._write_command("pause")
        self.status.lifecycle_state = "paused"
        self.status.message = "Paused by operator"
        await self.publish_status(self.status)

    async def resume(self) -> None:
        self._write_command("resume")
        self.status.lifecycle_state = "running"
        self.status.message = "Running"
        await self.publish_status(self.status)

    async def stop(self) -> None:
        self._write_command("stop")
        self.status.lifecycle_state = "stopped"
        self.status.message = "Stopped"
        await self.publish_status(self.status)

    async def handle_agent_exception(self, exc: Exception) -> None:
        self.last_error_message = str(exc)
        self.status.lifecycle_state = "error"
        self.status.message = f"Agent crashed: {exc}"
        await self.publish_status(self.status)

    async def publish_thought(self, thought: Thought) -> None:
        await self.thought_queue.put(thought)

    async def publish_log(self, log: LogEntry) -> None:
        await self.log_queue.put(log)

    async def mark_disconnected(self, reason: str) -> None:
        self.status.is_connected = False
        self.status.message = f"Disconnected: {reason}"
        await self.publish_status(self.status)

    async def mark_reconnected(self) -> None:
        self.status.is_connected = True
        self.status.message = "Connection restored"
        await self.publish_status(self.status)

    # ------------------------------------------------------------------
    def _write_command(self, command: str) -> None:
        path = self.control_dir / f"{command}.cmd"
        path.write_text(datetime.now().isoformat())
