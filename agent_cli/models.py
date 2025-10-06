"""Shared datamodels for the autonomous agent CLI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

LifecycleState = Literal["idle", "running", "paused", "error", "stopped"]
TaskStatus = Literal["pending", "in_progress", "completed", "failed"]
TaskPriority = Literal["low", "medium", "high"]
ThoughtType = Literal["reasoning", "planning", "reflecting"]
LogLevel = Literal["DEBUG", "INFO", "WARN", "ERROR"]
TestStatus = Literal["pass", "fail", "skip", "running"]


@dataclass
class AgentStatus:
    """Aggregate view of the agent lifecycle state for UI consumption."""

    lifecycle_state: LifecycleState
    cycle: int
    active_task: str
    progress: float
    message: str
    is_connected: bool
    updated_at: datetime

    def status_display(self) -> str:
        """Return a human readable lifecycle string."""
        base = self.lifecycle_state.capitalize()
        if not self.is_connected:
            return f"{base} (disconnected)"
        return base

    def progress_percent(self) -> int:
        """Convert the internal progress ratio to an integer percentage."""
        return max(0, min(100, int(round(self.progress * 100))))


@dataclass
class Task:
    """Task entry surfaced in the Task Manager panel."""

    id: int
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime


@dataclass
class Thought:
    """AI thought unit displayed in the Thinking panel."""

    cycle: int
    timestamp: datetime
    content: str
    thought_type: ThoughtType


@dataclass
class LogEntry:
    """Execution log line for the Logs panel."""

    cycle: int
    timestamp: datetime
    level: LogLevel
    message: str


@dataclass
class FileInfo:
    """Metadata describing a file in the code editor panel."""

    path: Path
    size: int
    modified: datetime
    is_readonly: bool = False


@dataclass
class ModelConfig:
    """Model configuration surfaced in the model config panel."""

    name: str
    provider: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.95

    def copy_with(
        self,
        *,
        name: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
    ) -> "ModelConfig":
        """Return a shallow copy with modifications applied."""
        return ModelConfig(
            name=name or self.name,
            provider=provider or self.provider,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
            top_p=self.top_p if top_p is None else top_p,
        )


@dataclass
class TestResult:
    """Test execution outcome tracked by the Verification panel."""

    name: str
    status: TestStatus
    duration_ms: float
    error_message: Optional[str] = None
    output: str = ""


__all__ = [
    "AgentStatus",
    "LifecycleState",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "Thought",
    "ThoughtType",
    "LogEntry",
    "LogLevel",
    "FileInfo",
    "ModelConfig",
    "TestResult",
    "TestStatus",
]
