"""Real agent manager that integrates with agent/run.py."""

import threading
import time
from datetime import datetime
from collections import deque
from pathlib import Path
from typing import Optional, List
import json

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

        # Ensure directories exist
        self.control_dir.mkdir(parents=True, exist_ok=True)
        self.state_root.mkdir(parents=True, exist_ok=True)

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
            self._add_log(LogLevel.INFO, "Agent continues running (design: never stop)")

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
        """Run the real agent loop - imports and executes agent/run.py."""
        try:
            # Import the real agent
            from agent.run import AgentLoop, load_config

            # Load config
            config_path = self.repo_root / "agent" / "config.json"
            cfg = load_config(config_path)

            # Override config for autonomous mode
            cfg.setdefault('loop', {})
            cfg['loop']['max_cycles'] = 0  # Never stop
            cfg['loop']['cooldown_seconds'] = 10  # Faster cycles
            cfg['loop']['apply_patches'] = True  # Auto-apply changes
            cfg['loop']['require_manual_approval'] = False  # No human intervention

            with self._lock:
                self._add_log(LogLevel.INFO, "Starting AgentLoop from agent/run.py")
                self.state.model = cfg.get('provider', {}).get('model', 'unknown')

            # Create and run agent loop
            agent_loop = AgentLoop(self.repo_root, cfg)

            # Monitor agent in separate thread
            monitor_thread = threading.Thread(target=self._monitor_agent, args=(agent_loop,), daemon=True)
            monitor_thread.start()

            # Run agent (blocks until stopped)
            agent_loop.run()

        except Exception as e:
            with self._lock:
                self._add_log(LogLevel.ERROR, f"Agent error: {str(e)}")
                self.state.status = AgentStatus.STOPPED

    def _monitor_agent(self, agent_loop):
        """Monitor agent execution and update dashboard state."""
        while not self._stop_flag and self.state.status == AgentStatus.RUNNING:
            try:
                # Read thinking logs
                thinking_log = self.state_root / "thinking.log"
                if thinking_log.exists():
                    # Parse recent thinking logs
                    with open(thinking_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines[-10:]:  # Last 10 lines
                            if line.strip():
                                with self._lock:
                                    thought = ThoughtEntry(
                                        cycle=self.state.cycle,
                                        timestamp=datetime.now(),
                                        content=line.strip()[:200]
                                    )
                                    self.thoughts.append(thought)

                # Update cycle count from artifacts
                artifact_root = Path(__file__).resolve().parent.parent.parent / "agent" / "artifacts"
                if artifact_root.exists():
                    cycle_dirs = list(artifact_root.glob("cycle_*"))
                    with self._lock:
                        self.state.cycle = len(cycle_dirs)

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                with self._lock:
                    self._add_log(LogLevel.ERROR, f"Monitor error: {e}")

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
