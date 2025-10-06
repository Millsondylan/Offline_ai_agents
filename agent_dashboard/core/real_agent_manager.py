"""Real agent manager that integrates with agent/run.py."""

import threading
import time
from datetime import datetime
from collections import deque
from pathlib import Path
from typing import Optional, List
import json

from agent.task_executor import TaskExecutor
from agent_dashboard.core.models import (
    AgentState, AgentStatus, AgentMode, Task, TaskStatus,
    ThoughtEntry, LogEntry, LogLevel
)


class RealAgentManager:
    """Manages real agent lifecycle using agent/run.py."""

    def __init__(self):
        self.state = AgentState()
        self.tasks: List[Task] = []
        self.thoughts: deque = deque(maxlen=1000)
        self.logs: deque = deque(maxlen=5000)
        self.active_task_id: Optional[int] = None

        self._lock = threading.Lock()
        self._agent_thread: Optional[threading.Thread] = None
        self._stop_flag = False
        self._start_time: Optional[float] = None

        # Paths
        self.repo_root = Path.cwd()
        self.local_root = Path(__file__).resolve().parent.parent.parent / "agent" / "local"
        self.control_dir = self.local_root / "control"
        self.task_file = self.control_dir / "task.txt"
        self.state_root = Path(__file__).resolve().parent.parent.parent / "agent" / "state"

        self.task_executor = TaskExecutor(self.repo_root)

        # Ensure directories exist
        self.control_dir.mkdir(parents=True, exist_ok=True)
        self.state_root.mkdir(parents=True, exist_ok=True)

        # Load model from config
        self._load_model_from_config()

        # Set real session ID
        self.state.session_id = str(int(time.time()))

        # Initial log
        self._add_log(LogLevel.INFO, "Dashboard initialized - autonomous agent ready")

    def start(self):
        """Start the real agent."""
        with self._lock:
            if self.state.status == AgentStatus.RUNNING:
                return

            self.state.status = AgentStatus.RUNNING
            self.state.cycle = 0
            self._start_time = time.time()
            self._stop_flag = False

        # Start agent thread
        self._agent_thread = threading.Thread(target=self._run_real_agent, daemon=True)
        self._agent_thread.start()

        with self._lock:
            self._add_log(LogLevel.INFO, "Real agent started - autonomous mode")

    def pause(self):
        """Pause the agent (not supported for autonomous agent)."""
        with self._lock:
            self._add_log(LogLevel.WARN, "Pause not supported in autonomous mode")

    def resume(self):
        """Resume the agent (not needed for autonomous agent)."""
        with self._lock:
            self._add_log(LogLevel.INFO, "Agent already running continuously")

    def stop(self):
        """Stop the agent."""
        with self._lock:
            self._add_log(LogLevel.WARN, "Stop requested but agent is designed to run continuously")
            # In truly autonomous mode, we don't stop
            # But we can mark it for user awareness
            self._add_log(LogLevel.INFO, f"Agent continues running (design: never stop)")

    def run_verification(self):
        """Run the verification suite."""
        with self._lock:
            self._add_log(LogLevel.INFO, "Verification run requested")
            task_id = self.task_executor.create_task("Manual Verification", "Running verification suite manually")
            self.task_executor.execute_task(task_id, lambda: True)

    def add_task(self, description: str) -> Task:
        """Add a new task to the queue."""
        with self._lock:
            task_id = max([t.id for t in self.tasks], default=0) + 1
            task = Task(
                id=task_id,
                description=description,
                status=TaskStatus.PENDING,
                created_at=datetime.now()
            )
            self.tasks.append(task)

            # Write task to control file for agent to pick up
            try:
                with open(self.task_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n[Task #{task_id}] {description}\n")
                self._add_log(LogLevel.INFO, f"Task #{task_id} queued: {description[:50]}...")
            except Exception as e:
                self._add_log(LogLevel.ERROR, f"Failed to write task: {e}")

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

                # Clear task file and write only this task
                try:
                    with open(self.task_file, 'w', encoding='utf-8') as f:
                        f.write(f"[Task #{task_id} - ACTIVE]\n{task.description}\n")
                    self._add_log(LogLevel.INFO, f"Activated task: {task.description[:50]}...")
                except Exception as e:
                    self._add_log(LogLevel.ERROR, f"Failed to activate task: {e}")

    def get_state(self) -> AgentState:
        """Get current agent state."""
        with self._lock:
            if self._start_time and self.state.status == AgentStatus.RUNNING:
                self.state.elapsed_seconds = int(time.time() - self._start_time)
            
            # Get state from task executor
            executor_state = self.task_executor.get_state()
            self.state.verification_checks = executor_state["verification_checks"]
            
            # Find active task and update state
            active_task = None
            for task in executor_state["tasks"]:
                if task["status"] == "running" or task["status"] == "verifying":
                    active_task = task
                    break
            
            if active_task:
                self.state.current_task = active_task["task_name"]
                self.state.progress_percent = int(active_task["progress"])
                self.state.cycle = active_task.get("cycle", 0)

            return self.state

    def get_thoughts(self) -> List[ThoughtEntry]:
        """Get all thoughts."""
        with self._lock:
            return list(self.thoughts)

    def get_logs(self) -> List[LogEntry]:
        """Get all logs."""
        with self._lock:
            return list(self.logs)

    def _run_real_agent(self):
        """Run the real agent loop using TaskExecutor."""
        try:
            with self._lock:
                self._add_log(LogLevel.INFO, "Starting TaskExecutor")

            # Run the task executor's continuous loop
            # This will block, but it's in a daemon thread so it's OK
            self.task_executor.run_continuously()

        except Exception as e:
            import traceback
            error_msg = f"Agent error: {str(e)}\n{traceback.format_exc()}"
            with self._lock:
                self._add_log(LogLevel.ERROR, error_msg)
                self.state.status = AgentStatus.ERROR

            # Write to file for debugging
            try:
                with open(self.state_root / "agent_error.log", "w") as f:
                    f.write(error_msg)
            except:
                pass

    def _load_model_from_config(self):
        """Load model name from config file."""
        try:
            config_path = self.repo_root / "agent" / "config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    model = config.get('provider', {}).get('model', 'Not configured')
                    self.state.model = model
            else:
                self.state.model = "No config found"
        except Exception:
            self.state.model = "Config error"

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
