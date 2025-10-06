"""State watcher that polls agent state files every 500ms."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ControlState:
    """Control panel state."""
    status: str = "idle"  # running, paused, stopped, idle
    provider: str = "unknown"
    model: str = "unknown"
    session_duration: int = 0
    cycle_count: int = 0
    cycle_status: str = "idle"
    available_models: List[str] = field(default_factory=list)


@dataclass
class CycleState:
    """Current cycle state."""
    cycle_number: int = 0
    phase: str = "idle"
    elapsed_seconds: int = 0
    estimated_seconds: int = 0
    fastpath_files: List[str] = field(default_factory=list)

    @property
    def elapsed(self) -> str:
        """Formatted elapsed time."""
        return f"{self.elapsed_seconds}s"

    @property
    def estimate(self) -> str:
        """Formatted estimated time."""
        if self.estimated_seconds > 0:
            return f"{self.estimated_seconds}s"
        return "--"

    @property
    def fastpath(self) -> str:
        """Formatted fastpath files."""
        if not self.fastpath_files:
            return "--"
        return ", ".join(self.fastpath_files[:3]) + ("..." if len(self.fastpath_files) > 3 else "")


@dataclass
class TaskState:
    """Task in the queue."""
    id: str
    name: str
    status: str  # running, paused, pending, complete

    @property
    def identifier(self) -> str:
        """Get task identifier (same as id)."""
        return self.id

    @property
    def title(self) -> str:
        """Get task title (same as name)."""
        return self.name


@dataclass
class GateState:
    """Production gate state."""
    name: str
    status: str  # passed, failed, running, pending
    findings_count: int = 0


@dataclass
class ArtifactState:
    """Artifact file state."""
    path: Path
    label: str
    type: str  # diff, findings, log, config, other

    @property
    def kind(self) -> str:
        """Get artifact kind (same as type)."""
        return self.type


@dataclass
class OutputState:
    """Output viewer state."""
    diff_text: str = ""
    findings: List[Dict] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    config_text: str = ""


@dataclass
class StateSnapshot:
    """Complete state snapshot."""
    control: ControlState = field(default_factory=ControlState)
    cycle: CycleState = field(default_factory=CycleState)
    tasks: List[TaskState] = field(default_factory=list)
    gates: List[GateState] = field(default_factory=list)
    artifacts: List[ArtifactState] = field(default_factory=list)
    output: OutputState = field(default_factory=OutputState)


class StateWatcher:
    """Polls agent state files and provides snapshots."""

    def __init__(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.state_root = self.repo_root / "agent" / "state"
        self.artifact_root = self.repo_root / "agent" / "artifacts"
        self.config_path = self.repo_root / "agent" / "config.json"

    def snapshot(self) -> StateSnapshot:
        """Create a complete state snapshot."""
        return StateSnapshot(
            control=self._read_control_state(),
            cycle=self._read_cycle_state(),
            tasks=self._read_tasks(),
            gates=self._read_gates(),
            artifacts=self._read_artifacts(),
            output=self._read_output(),
        )

    def _read_json(self, path: Path) -> Dict:
        """Read JSON file safely."""
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _read_control_state(self) -> ControlState:
        """Read control panel state."""
        session = self._read_json(self.state_root / "session.json")
        config = self._read_json(self.config_path)

        status = session.get("status", "idle")
        provider_data = config.get("provider", {})
        provider = provider_data.get("type", "unknown")
        model = provider_data.get("model", "unknown")
        cycle_count = session.get("cycle_count", 0)
        duration = session.get("session_duration", 0)
        cycle_status = session.get("phase", "idle")
        available_models = config.get("available_models", [])

        return ControlState(
            status=status,
            provider=provider,
            model=model,
            session_duration=duration,
            cycle_count=cycle_count,
            cycle_status=cycle_status,
            available_models=available_models,
        )

    def _read_cycle_state(self) -> CycleState:
        """Read current cycle state."""
        session = self._read_json(self.state_root / "session.json")

        cycle_num = session.get("current_cycle", 0)
        phase = session.get("phase", "idle")
        elapsed = session.get("elapsed_seconds", 0)
        estimated = session.get("estimated_seconds", 0)
        fastpath = session.get("fastpath_files", [])

        return CycleState(
            cycle_number=cycle_num,
            phase=phase,
            elapsed_seconds=elapsed,
            estimated_seconds=estimated,
            fastpath_files=fastpath,
        )

    def _read_tasks(self) -> List[TaskState]:
        """Read task queue."""
        scheduler = self._read_json(self.state_root / "scheduler.json")
        tasks_data = scheduler.get("tasks", [])

        tasks = []
        for i, task in enumerate(tasks_data):
            if isinstance(task, dict):
                task_id = task.get("id", f"task_{i}")
                name = task.get("name", "Unnamed task")
                status = task.get("status", "pending")
            else:
                task_id = f"task_{i}"
                name = str(task)
                status = "pending"

            tasks.append(TaskState(id=task_id, name=name, status=status))

        return tasks

    def _read_gates(self) -> List[GateState]:
        """Read production gate states."""
        latest_cycle = self._get_latest_cycle_dir()
        if not latest_cycle:
            return []

        meta = self._read_json(latest_cycle / "cycle.meta.json")
        gates_data = meta.get("gates", {})

        gates = []
        for name, info in gates_data.items():
            status = "passed" if info.get("passed") else "failed"
            findings = len(info.get("findings", []))
            gates.append(GateState(name=name, status=status, findings_count=findings))

        return gates

    def _read_artifacts(self) -> List[ArtifactState]:
        """Read artifact files."""
        if not self.artifact_root.exists():
            return []

        artifacts = []
        for cycle_dir in sorted(self.artifact_root.iterdir(), reverse=True):
            if not cycle_dir.is_dir():
                continue

            for file_path in cycle_dir.rglob("*"):
                if not file_path.is_file():
                    continue

                rel_path = file_path.relative_to(self.artifact_root)
                label = str(rel_path)

                # Determine type
                if file_path.suffix == ".patch" or "diff" in file_path.name:
                    file_type = "diff"
                elif file_path.suffix == ".json" and "findings" in file_path.name:
                    file_type = "findings"
                elif file_path.suffix == ".log":
                    file_type = "log"
                elif file_path.name == "config.json":
                    file_type = "config"
                else:
                    file_type = "other"

                artifacts.append(
                    ArtifactState(path=file_path, label=label, type=file_type)
                )

        return artifacts[:50]  # Limit to 50 most recent

    def _read_output(self) -> OutputState:
        """Read output viewer state."""
        latest_cycle = self._get_latest_cycle_dir()
        if not latest_cycle:
            return OutputState()

        # Read diff
        diff_text = ""
        for candidate in ["applied.patch", "proposed.patch", "diff.patch"]:
            diff_path = latest_cycle / candidate
            if diff_path.exists():
                try:
                    diff_text = diff_path.read_text(encoding="utf-8")
                    break
                except Exception:
                    pass

        # Read findings
        findings = []
        findings_path = latest_cycle / "findings.json"
        if findings_path.exists():
            findings_data = self._read_json(findings_path)
            if isinstance(findings_data, list):
                findings = findings_data
            elif isinstance(findings_data, dict):
                findings = findings_data.get("findings", [])

        # Read logs
        logs = []
        log_path = latest_cycle / "agent.log"
        if log_path.exists():
            try:
                logs = log_path.read_text(encoding="utf-8").splitlines()[-100:]
            except Exception:
                pass

        # Read config
        config_text = ""
        if self.config_path.exists():
            try:
                config_text = self.config_path.read_text(encoding="utf-8")
            except Exception:
                pass

        return OutputState(
            diff_text=diff_text,
            findings=findings,
            logs=logs,
            config_text=config_text,
        )

    def _get_latest_cycle_dir(self) -> Optional[Path]:
        """Get the latest cycle directory."""
        if not self.artifact_root.exists():
            return None

        cycle_dirs = [
            d for d in self.artifact_root.iterdir()
            if d.is_dir() and d.name.startswith("cycle_")
        ]

        return max(cycle_dirs, default=None) if cycle_dirs else None
