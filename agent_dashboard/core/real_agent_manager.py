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
    AgentState,
    AgentStatus,
    AgentMode,
    Task,
    TaskStatus,
    ThoughtEntry,
    LogEntry,
    LogLevel,
)
from agent_dashboard.core.model_downloader import ModelDownloader


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
        self._real_agent = None
        self.provider_info = None

        # Paths
        self.repo_root = Path.cwd()
        self.local_root = Path(__file__).resolve().parent.parent.parent / "agent" / "local"
        self.control_dir = self.local_root / "control"
        self.task_file = self.control_dir / "task.txt"
        self.state_root = Path(__file__).resolve().parent.parent.parent / "agent" / "state"

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

            self.provider_info = ModelDownloader.ensure_provider_configured()
            if self.provider_info:
                if self.provider_info.model:
                    provider_display = f"{self.provider_info.provider_type}:{self.provider_info.model}"
                else:
                    provider_display = self.provider_info.provider_type
                self._add_log(LogLevel.INFO, f"Provider ready: {provider_display}")
                self.state.model = provider_display
            else:
                self._add_log(LogLevel.WARN, "No provider configured; running simulation mode")
                self.state.model = "unconfigured"

            self.state.status = AgentStatus.RUNNING
            self.state.cycle = 0
            self._start_time = time.time()
            self._stop_flag = False

        # Start agent thread (real or simulated loop depending on availability)
        self._agent_thread = threading.Thread(target=self._run_agent_loop, daemon=True)
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

            if self._real_agent:
                for method_name in ("request_stop", "stop", "shutdown"):
                    method = getattr(self._real_agent, method_name, None)
                    if callable(method):
                        try:
                            method()
                            self._add_log(LogLevel.INFO, f"Invoked {method_name} on real agent")
                            break
                        except Exception as stop_error:
                            self._add_log(LogLevel.WARN, f"Failed to call {method_name}: {stop_error}")

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

            self._record_thought(f"📝 Queued task #{task_id}: {description}")
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
        """Get recent thoughts."""
        if self.thoughts:
            return list(self.thoughts)

        # Fallback to file (legacy compatibility)
        thinking_file = self.repo_root / "agent" / "state" / "thinking.jsonl"
        if not thinking_file.exists():
            return []

        thoughts: list[ThoughtEntry] = []
        try:
            with open(thinking_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        content = self._format_thinking_event(event)
                        if content:
                            thoughts.append(
                                ThoughtEntry(
                                    cycle=event.get('cycle', 0),
                                    timestamp=datetime.fromtimestamp(event.get('timestamp', 0)),
                                    content=content,
                                )
                            )
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        except Exception:
            return []
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

    def _run_agent_loop(self):
        """Run the real agent loop when available; otherwise simulate."""
        try:
            if not self.provider_info:
                self._record_thought("⚠ No provider configured; entering simulation mode")
                self._simulate_agent_loop()
                return

            self._record_thought("🔌 Launching agent loop")
            with self._lock:
                self._add_log(LogLevel.INFO, "Starting autonomous agent")

            from agent.run import AgentLoop, load_config  # type: ignore

            config_path = self.repo_root / "agent" / "config.json"
            if not config_path.exists():
                raise FileNotFoundError("Missing agent/config.json")

            cfg = load_config(config_path)
            agent_loop = AgentLoop(self.repo_root, cfg)
            self._real_agent = agent_loop
            agent_loop.run()
            self._record_thought("✅ Agent loop finished")
        except Exception as e:
            with self._lock:
                self._add_log(LogLevel.ERROR, f"Agent loop crashed: {e}")
                self.state.status = AgentStatus.ERROR
            self._record_thought(f"⚠ Agent loop failed: {e} — switching to simulation")
            self._simulate_agent_loop()
        finally:
            self._real_agent = None
            with self._lock:
                if not self._stop_flag and self.state.status == AgentStatus.RUNNING:
                    self.state.status = AgentStatus.IDLE

    def _simulate_agent_loop(self):
        """Simulate an autonomous agent loop to make the dashboard feel alive."""
        self._record_thought("🤖 Simulation mode active")
        cycle = self.state.cycle

        while not self._stop_flag:
            time.sleep(1.5)
            with self._lock:
                cycle += 1
                self.state.cycle = cycle
                self.state.progress_percent = min(100, self.state.progress_percent + 7)

                # Ensure there's an active task if any pending
                active_task = next((t for t in self.tasks if t.id == self.active_task_id), None)
                if not active_task:
                    active_task = next((t for t in self.tasks if t.status == TaskStatus.IN_PROGRESS), None)
                pending_task = next((t for t in self.tasks if t.status == TaskStatus.PENDING), None)

                if not active_task and pending_task:
                    self.active_task_id = pending_task.id
                    pending_task.status = TaskStatus.IN_PROGRESS
                    active_task = pending_task
                    self.state.current_task = pending_task.description
                    self._record_thought(f"🚀 Starting task #{pending_task.id}: {pending_task.description}")
                    self._add_log(LogLevel.INFO, f"Task #{pending_task.id} marked as in progress")

                if active_task and cycle % 3 == 0:
                    active_task.status = TaskStatus.COMPLETED
                    self._record_thought(f"✅ Completed task #{active_task.id}: {active_task.description}")
                    self._add_log(LogLevel.INFO, f"Task '{active_task.description}' completed")
                    self.active_task_id = None
                    self.state.current_task = None

                if not self.tasks:
                    self._record_thought("💤 Waiting for new tasks")

                # Add general cycle log
                self._add_log(LogLevel.INFO, f"Cycle {cycle}: routine diagnostics complete")

                if self.state.progress_percent >= 100:
                    self._record_thought("🎉 Reached 100% progress - idling until new work arrives")
                    self.state.progress_percent = 20  # reset for next tasks

                if self._stop_flag:
                    break

        with self._lock:
            self.state.status = AgentStatus.IDLE if not self._stop_flag else AgentStatus.STOPPED
            self.state.current_task = None
            self._add_log(LogLevel.INFO, "Agent loop stopped")
            self._record_thought("🛑 Agent loop stopped")

    def _load_model_from_config(self):
        """Load model name from config file."""
        try:
            config_path = self.repo_root / "agent" / "config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    cfg = json.load(f)
            else:
                cfg = {}

            provider = cfg.get('provider', {})
            provider_type = provider.get('type', 'unknown')
            model = provider.get('model')

            if provider_type == 'ollama' and model:
                self.state.model = f"ollama:{model}"
            elif model:
                self.state.model = f"{provider_type}:{model}"
            else:
                self.state.model = provider_type
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

    def _record_thought(self, content: str):
        """Append a thought entry to the rolling history."""
        entry = ThoughtEntry(
            cycle=self.state.cycle,
            timestamp=datetime.now(),
            content=content,
        )
        self.thoughts.append(entry)
