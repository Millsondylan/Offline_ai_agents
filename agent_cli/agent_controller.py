"""Agent controller responsible for orchestrating agent lifecycle and events."""

from __future__ import annotations

import asyncio
from asyncio import Queue
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Union

from agent_cli.models import AgentStatus, LogEntry, Thought


StatusCallback = Callable[[AgentStatus], None]
ThoughtCallback = Callable[[Thought], None]
LogCallback = Callable[[LogEntry], None]


class AgentController:
    """Coordinate agent commands and surface real-time telemetry to the UI."""

    def __init__(self, *, control_dir: Union[Path, str]) -> None:
        self.control_dir = Path(control_dir)
        self.control_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        self.status: AgentStatus = AgentStatus(
            lifecycle_state="idle",
            cycle=0,
            active_task="",
            progress=0.0,
            message="Idle",
            is_connected=True,
            updated_at=now,
        )
        self.status_queue: Queue[AgentStatus] = asyncio.Queue()
        self.thought_queue: Queue[Thought] = asyncio.Queue(maxsize=1000)
        self.log_queue: Queue[LogEntry] = asyncio.Queue(maxsize=5000)

        self._status_subscribers: List[StatusCallback] = []
        self._thought_subscribers: List[ThoughtCallback] = []
        self._log_subscribers: List[LogCallback] = []

        self._is_running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.last_error_message: Optional[str] = None

    # ------------------------------------------------------------------
    def subscribe_status(self, callback: StatusCallback) -> None:
        self._status_subscribers.append(callback)
        try:
            callback(self.status)
        except Exception:
            pass

    def subscribe_thoughts(self, callback: ThoughtCallback) -> None:
        self._thought_subscribers.append(callback)

    def subscribe_logs(self, callback: LogCallback) -> None:
        self._log_subscribers.append(callback)

    # ------------------------------------------------------------------
    async def start(self) -> None:
        if self._is_running:
            return
        self._loop = asyncio.get_running_loop()
        self._is_running = True
        await self._write_command("start.cmd")
        new_status = self._status_clone(lifecycle_state="running", message="Agent started", updated_at=datetime.now())
        self.status = new_status
        self._notify_status_subscribers(new_status)

    async def pause(self) -> None:
        if not self._is_running:
            return
        await self._write_command("pause.cmd")
        await self._emit_status(
            self._status_clone(lifecycle_state="paused", message="Paused by user", updated_at=datetime.now())
        )

    async def resume(self) -> None:
        if not self._is_running:
            return
        await self._write_command("resume.cmd")
        await self._emit_status(
            self._status_clone(lifecycle_state="running", message="Resumed", updated_at=datetime.now())
        )

    async def stop(self) -> None:
        await self._write_command("stop.cmd")
        self._is_running = False
        await self._emit_status(
            self._status_clone(lifecycle_state="stopped", message="Agent stopped", updated_at=datetime.now())
        )

    # ------------------------------------------------------------------
    async def publish_status(self, status: AgentStatus) -> None:
        await self._emit_status(status)

    async def publish_thought(self, thought: Thought) -> None:
        await self.thought_queue.put(thought)
        for callback in list(self._thought_subscribers):
            try:
                callback(thought)
            except Exception:
                continue

    async def publish_log(self, log: LogEntry) -> None:
        await self.log_queue.put(log)
        for callback in list(self._log_subscribers):
            try:
                callback(log)
            except Exception:
                continue

    async def handle_agent_exception(self, error: Exception) -> None:
        self.last_error_message = str(error)
        await self._emit_status(
            self._status_clone(
                lifecycle_state="error",
                message=f"Agent error: {error}",
                is_connected=False,
                updated_at=datetime.now(),
            )
        )

    async def mark_disconnected(self, reason: str) -> None:
        await self._emit_status(
            self._status_clone(
                message=f"Disconnected: {reason}",
                is_connected=False,
                updated_at=datetime.now(),
            )
        )

    async def mark_reconnected(self) -> None:
        await self._emit_status(
            self._status_clone(
                message="Connection restored",
                is_connected=True,
                updated_at=datetime.now(),
            )
        )

    # ------------------------------------------------------------------
    async def _emit_status(self, status: AgentStatus) -> None:
        self.status = status
        await self.status_queue.put(status)
        self._notify_status_subscribers(status)

    async def _write_command(self, filename: str) -> None:
        path = self.control_dir / filename
        await asyncio.to_thread(path.write_text, "")

    def _status_clone(self, **overrides) -> AgentStatus:
        base = self.status
        return AgentStatus(
            lifecycle_state=overrides.get("lifecycle_state", base.lifecycle_state),
            cycle=overrides.get("cycle", base.cycle),
            active_task=overrides.get("active_task", base.active_task),
            progress=overrides.get("progress", base.progress),
            message=overrides.get("message", base.message),
            is_connected=overrides.get("is_connected", base.is_connected),
            updated_at=overrides.get("updated_at", datetime.now()),
        )

    def _notify_status_subscribers(self, status: AgentStatus) -> None:
        for callback in list(self._status_subscribers):
            try:
                callback(status)
            except Exception:
                continue


__all__ = ["AgentController"]
