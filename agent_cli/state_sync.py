"""State synchronization helpers bridging agent state files to panels."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set, Tuple

from agent_cli.models import AgentStatus, LogEntry, Thought
from agent_cli.panels.home import HomePanel
from agent_cli.panels.logs import LogsPanel
from agent_cli.panels.thinking import ThinkingPanel
from agent_cli.ui_manager import UIManager

try:
    from agent.tui.state_watcher import StateSnapshot, StateWatcher, ThinkingEvent
except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
    raise RuntimeError("StateWatcher module not available; ensure agent package is on PYTHONPATH") from exc


class StateSynchronizer:
    """Poll `StateWatcher` snapshots and update panels/UI accordingly."""

    def __init__(
        self,
        *,
        watcher: StateWatcher,
        ui: UIManager,
        home_panel: HomePanel,
        thinking_panel: ThinkingPanel,
        logs_panel: LogsPanel,
        poll_interval: float = 0.5,
    ) -> None:
        self.watcher = watcher
        self.ui = ui
        self.home_panel = home_panel
        self.thinking_panel = thinking_panel
        self.logs_panel = logs_panel
        self.poll_interval = poll_interval

        self._seen_thoughts: Set[Tuple[float, Optional[int], str]] = set()
        self._seen_logs: Set[str] = set()

    async def run(self) -> None:
        while True:
            snapshot = await asyncio.to_thread(self.watcher.snapshot)
            self._apply_snapshot(snapshot)
            await asyncio.sleep(self.poll_interval)

    def _apply_snapshot(self, snapshot: StateSnapshot) -> None:
        status = self._status_from_snapshot(snapshot)
        self.ui.update_status(status)
        self._update_home_panel(snapshot, status)
        self._update_thinking(snapshot)
        self._update_logs(snapshot)

    def _status_from_snapshot(self, snapshot: StateSnapshot) -> AgentStatus:
        control = snapshot.control
        cycle = snapshot.cycle.cycle_number or 0
        active_task = snapshot.tasks[0].name if snapshot.tasks else ""
        message = control.cycle_status or "Idle"
        progress = 0.0
        if snapshot.cycle.estimated_seconds:
            total = snapshot.cycle.estimated_seconds or 1
            progress = min(1.0, snapshot.cycle.elapsed_seconds / max(1, total))
        return AgentStatus(
            lifecycle_state=control.status or "idle",
            cycle=cycle,
            active_task=active_task,
            progress=progress,
            message=message,
            is_connected=True,
            updated_at=datetime.now(),
        )

    def _update_home_panel(self, snapshot: StateSnapshot, status: AgentStatus) -> None:
        total_tasks = len(snapshot.tasks)
        completed = sum(1 for task in snapshot.tasks if task.status == "complete")
        log_entries = len(snapshot.output.logs)
        self.home_panel.update_overview(
            status=status,
            total_tasks=total_tasks,
            completed_tasks=completed,
            log_entries=log_entries,
        )

    def _update_thinking(self, snapshot: StateSnapshot) -> None:
        for event in snapshot.output.thinking_events:
            key = (event.timestamp, event.cycle, event.event_type)
            if key in self._seen_thoughts:
                continue
            content = self._format_thinking_event(event)
            if not content:
                continue
            thought = Thought(
                cycle=event.cycle or 0,
                timestamp=datetime.fromtimestamp(event.timestamp) if event.timestamp else datetime.now(),
                content=content,
                thought_type=event.event_type or "reasoning",
            )
            self.thinking_panel.add_thought(thought)
            self._seen_thoughts.add(key)

    def _format_thinking_event(self, event: ThinkingEvent) -> Optional[str]:
        data = event.data or {}
        content = data.get("content") or data.get("message")
        if content:
            return content
        if data:
            return str(data)
        return None

    def _update_logs(self, snapshot: StateSnapshot) -> None:
        for line in snapshot.output.logs:
            if line in self._seen_logs:
                continue
            level, message = self._parse_log_line(line)
            entry = LogEntry(
                cycle=snapshot.cycle.cycle_number or 0,
                timestamp=datetime.now(),
                level=level,
                message=message,
            )
            self.logs_panel.add_log(entry)
            self._seen_logs.add(line)

    def _parse_log_line(self, line: str) -> Tuple[str, str]:
        if line.startswith("[") and "]" in line:
            closing = line.find("]")
            token = line[1:closing].strip().upper()
            message = line[closing + 1 :].strip()
            if token in {"DEBUG", "INFO", "WARN", "WARNING", "ERROR"}:
                if token == "WARNING":
                    token = "WARN"
                return token, message
        return "INFO", line


__all__ = ["StateSynchronizer"]
