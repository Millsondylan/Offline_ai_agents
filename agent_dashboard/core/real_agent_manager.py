"""Real agent manager that integrates with agent/run.py."""

import threading
import time
from datetime import datetime
from collections import deque
from pathlib import Path
from typing import Optional, List
import json

# TaskExecutor no longer needed - using real agent loop directly
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

        # Note: We no longer use TaskExecutor for running the agent
        # The real agent loop is started directly in _run_real_agent

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
            if self.state.status != AgentStatus.RUNNING:
                return

            self._add_log(LogLevel.INFO, "Stopping agent...")
            self._stop_flag = True

            # Signal the real agent to stop by creating a control command
            try:
                stop_cmd_file = self.control_dir / "stop.cmd"
                stop_cmd_file.write_text("stop\n", encoding="utf-8")
                self._add_log(LogLevel.INFO, "Stop signal sent to agent")
            except Exception as e:
                self._add_log(LogLevel.ERROR, f"Failed to send stop signal: {e}")

            # Wait for the agent thread to finish
            if self._agent_thread and self._agent_thread.is_alive():
                self._agent_thread.join(timeout=10)  # Give it more time to finish cycle

            self.state.status = AgentStatus.STOPPED
            self._agent_thread = None
            self._add_log(LogLevel.INFO, "Agent stopped.")

    def run_verification(self):
        """Run the verification suite."""
        with self._lock:
            self._add_log(LogLevel.INFO, "Verification run requested - will be handled by real agent cycle")

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

            # Write task to control file for real agent to pick up
            try:
                # The real agent reads from agent/local/control/task.txt
                # Overwrite the file with the new task (agent processes one task at a time)
                with open(self.task_file, 'w', encoding='utf-8') as f:
                    f.write(f"{description}\n")
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

            # Read state from real agent artifacts and state files
            self._update_state_from_artifacts()

            return self.state

    def _update_state_from_artifacts(self):
        """Update state by reading real agent's artifacts and state files."""
        try:
            # First, read from thinking.jsonl for real-time status
            thinking_file = self.repo_root / "agent" / "state" / "thinking.jsonl"
            if thinking_file.exists():
                try:
                    import json
                    # Read the last few lines to get latest status
                    with open(thinking_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    # Find the latest cycle and current activity
                    latest_cycle = 0
                    latest_activity = None

                    for line in reversed(lines[-20:]):  # Check last 20 entries
                        try:
                            event = json.loads(line.strip())
                            cycle = event.get('cycle', 0)
                            if cycle > latest_cycle:
                                latest_cycle = cycle

                            # Get current activity
                            event_type = event.get('event_type')
                            data = event.get('data', {})

                            if event_type == 'thinking':
                                content = data.get('content', '')
                                if content and not latest_activity:
                                    latest_activity = f"Thinking: {content}"
                            elif event_type == 'action':
                                action = data.get('action', '')
                                details = data.get('details', '')
                                status = data.get('status', '')
                                if action and not latest_activity:
                                    if status == 'started':
                                        latest_activity = f"Running: {action}"
                                    elif status == 'completed':
                                        latest_activity = f"Completed: {action}"
                                    else:
                                        latest_activity = f"Action: {action}"

                        except (json.JSONDecodeError, KeyError):
                            continue

                    if latest_cycle > 0:
                        self.state.cycle = latest_cycle
                        self.state.progress_percent = min(50 + (latest_cycle * 10), 90)

                    if latest_activity:
                        self.state.current_task = latest_activity

                except Exception:
                    pass

            # Fallback: Read latest cycle from artifacts directory
            artifacts_dir = self.repo_root / "agent" / "artifacts"
            if artifacts_dir.exists():
                cycle_dirs = [d for d in artifacts_dir.iterdir() if d.is_dir() and d.name.startswith("cycle_")]
                if cycle_dirs:
                    latest_cycle = max(cycle_dirs, key=lambda d: d.name)
                    cycle_num = int(latest_cycle.name.split("_")[1])
                    if cycle_num > self.state.cycle:  # Only update if higher than thinking log
                        self.state.cycle = cycle_num

            # Read task from control file if no current task found
            if not self.state.current_task or self.state.current_task == "None":
                task_file = self.repo_root / "agent" / "local" / "control" / "task.txt"
                if task_file.exists():
                    try:
                        task_content = task_file.read_text(encoding="utf-8").strip()
                        if task_content:
                            self.state.current_task = f"User task: {task_content[:50]}..."
                            if self.state.cycle == 0:
                                self.state.progress_percent = 5  # Task loaded but not started
                    except Exception:
                        pass
        except Exception:
            # Don't crash on state reading errors
            pass

    def get_thoughts(self) -> List[ThoughtEntry]:
        """Get all thoughts from the thinking logger."""
        thinking_file = self.repo_root / "agent" / "state" / "thinking.jsonl"
        thoughts = []

        if not thinking_file.exists():
            return thoughts

        try:
            import json
            from datetime import datetime

            with open(thinking_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())

                        # Convert thinking events to ThoughtEntry
                        if event.get('event_type') in ['thinking', 'action', 'decision', 'verification', 'model_interaction', 'code_generation', 'cycle_start', 'cycle_end']:
                            content = self._format_thinking_event(event)
                            if content:
                                thought = ThoughtEntry(
                                    cycle=event.get('cycle', 0),
                                    timestamp=datetime.fromtimestamp(event.get('timestamp', 0)),
                                    content=content
                                )
                                thoughts.append(thought)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue

        except Exception:
            # Don't crash if there are file reading issues
            pass

        # Return most recent thoughts (last 100)
        return thoughts[-100:]

    def _format_thinking_event(self, event: dict) -> str:
        """Format a thinking event for display in the dashboard."""
        event_type = event.get('event_type', 'unknown')
        data = event.get('data', {})

        if event_type == 'cycle_start':
            cycle = data.get('cycle', '?')
            return f"🔄 Starting cycle {cycle}"
        elif event_type == 'cycle_end':
            cycle = data.get('cycle', '?')
            return f"✅ Completed cycle {cycle}"
        elif event_type == 'thinking':
            thinking_type = data.get('type', 'general')
            content = data.get('content', '')
            return f"🤔 {thinking_type.title()}: {content}"
        elif event_type == 'action':
            action = data.get('action', 'unknown')
            details = data.get('details', '')
            status = data.get('status', '')
            status_icon = "✅" if status == "completed" else "⚡" if status == "started" else "❌" if status == "failed" else ""
            return f"{status_icon} Action: {action} - {details}"
        elif event_type == 'decision':
            decision = data.get('decision', 'unknown')
            details = data.get('details', '')
            return f"🎯 Decision: {decision} - {details}"
        elif event_type == 'verification':
            tool = data.get('tool', 'unknown')
            result = data.get('result', 'unknown')
            details = data.get('details', '')
            return f"🔍 Verification: {tool} -> {result} - {details}"
        elif event_type == 'model_interaction':
            model = data.get('model', 'unknown')
            interaction_type = data.get('interaction_type', 'unknown')
            details = data.get('details', '')
            return f"🤖 Model: {model} ({interaction_type}) - {details}"
        elif event_type == 'code_generation':
            language = data.get('language', 'unknown')
            details = data.get('details', '')
            return f"💻 Code: {language} - {details}"
        else:
            # Fallback for any other event types
            content = data.get('content', data.get('details', data.get('message', str(data))))
            return f"📝 {event_type}: {content}"

    def get_logs(self) -> List[LogEntry]:
        """Get all logs."""
        with self._lock:
            return list(self.logs)

    def _run_real_agent(self):
        """Run the real agent loop using the actual AgentLoop."""
        try:
            with self._lock:
                self._add_log(LogLevel.INFO, "Starting real autonomous agent")

            # Import and run the real agent loop
            from agent.run import AgentLoop, load_config

            config_path = self.repo_root / "agent" / "config.json"
            cfg = load_config(config_path)

            agent_loop = AgentLoop(self.repo_root, cfg)

            # Run the real agent loop
            # This will run until max_cycles or until the thread is interrupted
            agent_loop.run()

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
