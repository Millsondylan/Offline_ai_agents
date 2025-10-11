"""Agent management and communication."""

import threading
import time
from datetime import datetime
from collections import deque
from typing import Optional, Callable, List

from agent_dashboard.core.models import (
    AgentState, AgentStatus, AgentMode, Task, TaskStatus,
    ThoughtEntry, LogEntry, LogLevel
)


class AgentManager:
    """Manages agent lifecycle and communication."""

    def __init__(self):
        self.state = AgentState()
        self.tasks: List[Task] = []
        self.thoughts: deque = deque(maxlen=1000)
        self.logs: deque = deque(maxlen=5000)
        self.active_task_id: Optional[int] = None

        self._lock = threading.Lock()
        self._running_thread: Optional[threading.Thread] = None
        self._stop_flag = False
        self._start_time: Optional[float] = None

    def start(self):
        """Start the agent."""
        with self._lock:
            if self.state.status == AgentStatus.RUNNING:
                return

            self.state.status = AgentStatus.RUNNING
            self.state.cycle = 0
            self._start_time = time.time()
            self._stop_flag = False

            # Start agent thread
            self._running_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._running_thread.start()

            self._add_log(LogLevel.INFO, "Agent started")

    def pause(self):
        """Pause the agent."""
        with self._lock:
            if self.state.status != AgentStatus.RUNNING:
                return
            self.state.status = AgentStatus.PAUSED
            self._add_log(LogLevel.INFO, "Agent paused")

    def resume(self):
        """Resume the agent."""
        with self._lock:
            if self.state.status != AgentStatus.PAUSED:
                return
            self.state.status = AgentStatus.RUNNING
            self._add_log(LogLevel.INFO, "Agent resumed")

    def stop(self):
        """Stop the agent."""
        with self._lock:
            if self.state.status in (AgentStatus.IDLE, AgentStatus.STOPPED):
                return

            self._stop_flag = True
            self.state.status = AgentStatus.STOPPED
            self._add_log(LogLevel.INFO, "Agent stopped")

            if self._running_thread:
                self._running_thread = None

    def add_task(self, description: str) -> Task:
        """Add a new task."""
        with self._lock:
            task_id = max([t.id for t in self.tasks], default=0) + 1
            task = Task(
                id=task_id,
                description=description,
                status=TaskStatus.PENDING,
                created_at=datetime.now()
            )
        self.tasks.append(task)
        self._add_log(LogLevel.INFO, f"Created task #{task_id}: {description}")
        self.thoughts.append(ThoughtEntry(
            cycle=self.state.cycle,
            timestamp=datetime.now(),
            content=f"📝 Queued task #{task_id}: {description}",
        ))
        return task

    def delete_task(self, task_id: int):
        """Delete a task."""
        with self._lock:
            self.tasks = [t for t in self.tasks if t.id != task_id]
            self._add_log(LogLevel.INFO, f"Deleted task #{task_id}")

    def set_active_task(self, task_id: int):
        """Set the active task."""
        with self._lock:
            task = next((t for t in self.tasks if t.id == task_id), None)
            if task:
                self.active_task_id = task_id
                self.state.current_task = task.description
                task.status = TaskStatus.IN_PROGRESS
                self._add_log(LogLevel.INFO, f"Set active task: {task.description}")

    def get_state(self) -> AgentState:
        """Get current agent state."""
        with self._lock:
            if self._start_time and self.state.status == AgentStatus.RUNNING:
                self.state.elapsed_seconds = int(time.time() - self._start_time)
                if self.state.max_cycles > 0:
                    self.state.progress_percent = int(
                        (self.state.cycle / self.state.max_cycles) * 100
                    )
            return self.state

    def get_thoughts(self) -> List[ThoughtEntry]:
        """Get all thoughts."""
        with self._lock:
            return list(self.thoughts)

    def get_logs(self) -> List[LogEntry]:
        """Get all logs."""
        with self._lock:
            return list(self.logs)

    def _run_loop(self):
        """Main agent execution loop."""
        while not self._stop_flag:
            if self.state.status == AgentStatus.PAUSED:
                time.sleep(0.1)
                continue

            if self.state.status != AgentStatus.RUNNING:
                break

            # Simulate agent cycle
            with self._lock:
                self.state.cycle += 1

                # Add thought
                thought = ThoughtEntry(
                    cycle=self.state.cycle,
                    timestamp=datetime.now(),
                    content=f"Cycle {self.state.cycle}: Processing task..."
                )
                self.thoughts.append(thought)

                # Add log
                self._add_log(LogLevel.INFO, f"Completed cycle {self.state.cycle}")

                # Check if done
                if self.state.cycle >= self.state.max_cycles:
                    self.state.status = AgentStatus.STOPPED
                    self._add_log(LogLevel.INFO, "Reached max cycles")
                    break

            time.sleep(1)  # Simulate work

    def _add_log(self, level: LogLevel, message: str):
        """Add a log entry (must be called with lock held)."""
        log = LogEntry(
            cycle=self.state.cycle,
            timestamp=datetime.now(),
            level=level,
            message=message
        )
        self.logs.append(log)

        if level == LogLevel.ERROR:
            self.state.errors += 1
        elif level == LogLevel.WARN:
            self.state.warnings += 1
