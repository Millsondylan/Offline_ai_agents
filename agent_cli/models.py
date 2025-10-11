"""Light-weight data models consumed by the dashboard facade."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AgentStatus:
    """Represents the high-level lifecycle information for the agent."""

    lifecycle_state: str = "idle"
    cycle: int = 0
    active_task: str = ""
    progress: float = 0.0
    message: str = "Idle"
    is_connected: bool = True
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def progress_percent(self) -> int:
        """Progress expressed as an integer percentage."""
        return max(0, min(100, int(self.progress * 100)))

    @property
    def display_state(self) -> str:
        """Capitalised lifecycle state used in UI surfaces."""
        return self.lifecycle_state.capitalize()


@dataclass
class Thought:
    """Single reasoning entry streamed from the agent."""

    cycle: int
    timestamp: datetime
    content: str
    thought_type: str = "reasoning"


@dataclass
class LogEntry:
    """Structured execution log entry."""

    cycle: int
    timestamp: datetime
    level: str
    message: str


@dataclass
class Task:
    """User defined work item tracked inside the dashboard."""

    id: int
    description: str
    priority: str = "medium"
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"


@dataclass
class TestResult:
    """Outcome of a verification/test run."""

    name: str
    status: str
    duration_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


# Prevent pytest from collecting dataclasses named like tests.
TestResult.__test__ = False  # type: ignore[attr-defined]
