"""Data models for the agent dashboard."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class AgentMode(str, Enum):
    """Agent execution mode."""
    AUTO = "Auto"
    MANUAL = "Manual"
    FAST = "Fast"


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"


class LogLevel(str, Enum):
    """Log entry level."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class AgentState:
    """Complete agent state."""
    status: AgentStatus = AgentStatus.IDLE
    mode: AgentMode = AgentMode.AUTO
    model: str = "Detecting..."
    session_id: str = "0"
    cycle: int = 0
    max_cycles: int = 0  # 0 = infinite (never stops)
    elapsed_seconds: int = 0
    progress_percent: int = 0
    current_task: Optional[str] = None
    memory_mb: int = 0
    errors: int = 0
    warnings: int = 0
    verification_checks: list = field(default_factory=list)


@dataclass
class Task:
    """Task/goal for the agent."""
    id: int
    description: str
    status: TaskStatus
    created_at: datetime
    priority: int = 0


@dataclass
class ThoughtEntry:
    """AI reasoning thought."""
    cycle: int
    timestamp: datetime
    content: str


@dataclass
class LogEntry:
    """Execution log entry."""
    cycle: int
    timestamp: datetime
    level: LogLevel
    message: str


@dataclass
class FileEntry:
    """Code file entry."""
    path: str
    name: str
    size: int
    modified: datetime


@dataclass
class TestResult:
    """Verification test result."""
    name: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
