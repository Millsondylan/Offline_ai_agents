"""Data models for the agent control panel."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal, Optional


class AgentState(str, Enum):
    """Agent execution states."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LogLevel(str, Enum):
    """Log entry severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class ThoughtType(str, Enum):
    """Types of agent thoughts."""

    REASONING = "reasoning"
    PLANNING = "planning"
    REFLECTING = "reflecting"
    OBSERVING = "observing"


class TestStatus(str, Enum):
    """Test execution status."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    RUNNING = "running"


@dataclass
class AgentStatus:
    """Current agent state and metrics."""

    state: AgentState
    current_cycle: int
    total_cycles: int
    model_name: str
    provider: str
    session_duration_seconds: float
    active_task_id: Optional[int] = None
    last_error: Optional[str] = None
    thoughts_count: int = 0
    actions_count: int = 0


@dataclass
class Task:
    """User-defined task for the agent."""

    id: int
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class Thought:
    """AI agent reasoning step."""

    cycle: int
    timestamp: datetime
    content: str
    thought_type: ThoughtType


@dataclass
class LogEntry:
    """Execution log entry."""

    cycle: int
    timestamp: datetime
    level: LogLevel
    message: str
    stack_trace: Optional[str] = None


@dataclass
class ModelConfig:
    """AI model configuration."""

    name: str
    provider: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.95
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


@dataclass
class TestResult:
    """Test execution result."""

    name: str
    status: TestStatus
    duration_ms: float
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None


@dataclass
class FileInfo:
    """File metadata for code viewer."""

    path: Path
    size_bytes: int
    modified_at: datetime
    is_readonly: bool
    line_count: int = 0
