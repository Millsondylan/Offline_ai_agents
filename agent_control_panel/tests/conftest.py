"""Pytest configuration and shared fixtures."""

import curses
from collections import deque
from datetime import datetime
from typing import Any, Callable
from unittest.mock import Mock, MagicMock

import pytest

from agent_control_panel.core.models import (
    AgentState,
    AgentStatus,
    LogEntry,
    LogLevel,
    ModelConfig,
    Task,
    TaskPriority,
    TaskStatus,
    Thought,
    ThoughtType,
)


@pytest.fixture
def mock_stdscr():
    """Create a mock curses window for testing."""
    screen = MagicMock()
    screen.getmaxyx.return_value = (24, 80)  # Standard terminal size
    screen.getch.return_value = -1  # No input by default
    screen.getkey.return_value = ""
    return screen


@pytest.fixture
def sample_agent_status() -> AgentStatus:
    """Create a sample agent status for testing."""
    return AgentStatus(
        state=AgentState.RUNNING,
        current_cycle=42,
        total_cycles=100,
        model_name="gpt-4",
        provider="openai",
        session_duration_seconds=125.5,
        active_task_id=1,
        thoughts_count=156,
        actions_count=42,
    )


@pytest.fixture
def sample_tasks() -> list[Task]:
    """Create sample tasks for testing."""
    now = datetime.now()
    return [
        Task(
            id=1,
            description="Implement feature X",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            created_at=now,
            updated_at=now,
        ),
        Task(
            id=2,
            description="Fix bug in module Y",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            created_at=now,
            updated_at=now,
        ),
        Task(
            id=3,
            description="Write documentation",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.LOW,
            created_at=now,
            updated_at=now,
            completed_at=now,
        ),
    ]


@pytest.fixture
def sample_thoughts() -> deque[Thought]:
    """Create sample thoughts for testing."""
    now = datetime.now()
    return deque(
        [
            Thought(
                cycle=42,
                timestamp=now,
                content="Analyzing requirements for feature X",
                thought_type=ThoughtType.REASONING,
            ),
            Thought(
                cycle=42,
                timestamp=now,
                content="Planning implementation steps:\n  1. Update schema\n  2. Add logic\n  3. Write tests",
                thought_type=ThoughtType.PLANNING,
            ),
            Thought(
                cycle=43,
                timestamp=now,
                content="Executing step 1: Updating schema",
                thought_type=ThoughtType.OBSERVING,
            ),
        ],
        maxlen=1000,
    )


@pytest.fixture
def sample_logs() -> deque[LogEntry]:
    """Create sample log entries for testing."""
    now = datetime.now()
    return deque(
        [
            LogEntry(
                cycle=42,
                timestamp=now,
                level=LogLevel.INFO,
                message="Starting test suite",
            ),
            LogEntry(
                cycle=42,
                timestamp=now,
                level=LogLevel.ERROR,
                message="Test failed: config.yaml not found",
                stack_trace="File 'config.yaml', line 1234",
            ),
            LogEntry(
                cycle=43,
                timestamp=now,
                level=LogLevel.INFO,
                message="Retrying with default config",
            ),
        ],
        maxlen=5000,
    )


@pytest.fixture
def sample_model_config() -> ModelConfig:
    """Create a sample model configuration."""
    return ModelConfig(
        name="gpt-4",
        provider="openai",
        temperature=0.7,
        max_tokens=2048,
        top_p=0.95,
    )


@pytest.fixture
def mock_agent_controller():
    """Create a mock agent controller for testing."""
    controller = Mock()
    controller.get_status.return_value = AgentStatus(
        state=AgentState.IDLE,
        current_cycle=0,
        total_cycles=0,
        model_name="gpt-4",
        provider="openai",
        session_duration_seconds=0.0,
    )
    controller.start.return_value = None
    controller.pause.return_value = None
    controller.stop.return_value = None
    controller.is_running.return_value = False
    return controller


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager for testing."""
    manager = Mock()
    manager.get.return_value = None
    manager.set.return_value = None
    manager.save.return_value = None
    manager.load.return_value = None
    return manager
