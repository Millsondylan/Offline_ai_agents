"""Filesystem-based state watcher for the compatibility TUI."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class ControlSnapshot:
    status: str = "idle"
    cycle_count: int = 0
    session_duration: int = 0
    phase: str = ""
    provider: str = ""
    model: str = ""
    available_models: List[str] = field(default_factory=list)


@dataclass
class TaskSnapshot:
    id: str
    name: str
    status: str


@dataclass
class GateSnapshot:
    name: str
    status: str
    findings: List[dict] = field(default_factory=list)


@dataclass
class ArtifactSnapshot:
    cycle: str
    path: Path
    kind: str


@dataclass
class OutputSnapshot:
    config_text: str = ""
    diff_text: str = ""


@dataclass
class StateSnapshot:
    control: ControlSnapshot
    tasks: List[TaskSnapshot]
    gates: List[GateSnapshot]
    artifacts: List[ArtifactSnapshot]
    output: OutputSnapshot


class StateWatcher:
    """Loads agent state, tasks, gates, and artifacts from disk."""

    def __init__(self) -> None:
        self.state_root = Path("agent_state")
        self.artifact_root = Path("agent_artifacts")
        self.config_path = Path("agent_config.json")

    # ------------------------------------------------------------------
    def snapshot(self) -> StateSnapshot:
        control = ControlSnapshot()
        tasks: List[TaskSnapshot] = []
        gates: List[GateSnapshot] = []
        artifacts: List[ArtifactSnapshot] = []
        output = OutputSnapshot()

        # Control/session information
        session_path = self.state_root / "session.json"
        if session_path.exists():
            try:
                session_data = json.loads(session_path.read_text())
                control.status = session_data.get("status", control.status)
                control.cycle_count = session_data.get("cycle_count", control.cycle_count)
                control.session_duration = session_data.get("session_duration", control.session_duration)
                control.phase = session_data.get("phase", control.phase)
            except json.JSONDecodeError:
                pass

        # Config/provider information
        if self.config_path and self.config_path.exists():
            try:
                config_text = self.config_path.read_text()
                output.config_text = config_text
                config_data = json.loads(config_text)
                provider = config_data.get("provider", {})
                if isinstance(provider, dict):
                    control.provider = provider.get("type", "")
                    control.model = provider.get("model", "")
                models = config_data.get("available_models", [])
                if isinstance(models, list):
                    control.available_models = models
            except (OSError, json.JSONDecodeError):
                pass

        # Tasks
        scheduler_path = self.state_root / "scheduler.json"
        if scheduler_path.exists():
            try:
                scheduler = json.loads(scheduler_path.read_text())
                for item in scheduler.get("tasks", []):
                    tasks.append(
                        TaskSnapshot(
                            id=str(item.get("id", "")),
                            name=item.get("name", ""),
                            status=item.get("status", ""),
                        )
                    )
            except json.JSONDecodeError:
                pass

        # Gates and artifacts
        if self.artifact_root.exists():
            for cycle_dir in sorted(self.artifact_root.glob("cycle_*")):
                if not cycle_dir.is_dir():
                    continue
                cycle_name = cycle_dir.name

                meta = cycle_dir / "cycle.meta.json"
                if meta.exists():
                    try:
                        meta_data = json.loads(meta.read_text())
                        gates_data = meta_data.get("gates", {})
                        for name, info in gates_data.items():
                            status = "passed" if info.get("passed") else "failed"
                            gates.append(
                                GateSnapshot(
                                    name=name,
                                    status=status,
                                    findings=info.get("findings", []),
                                )
                            )
                    except json.JSONDecodeError:
                        pass

                for file_path in sorted(cycle_dir.iterdir()):
                    if file_path.is_file():
                        kind = file_path.suffix.lstrip(".") or "file"
                        artifacts.append(ArtifactSnapshot(cycle=cycle_name, path=file_path, kind=kind))
                        if not output.diff_text and file_path.suffix in {".diff", ".patch"}:
                            output.diff_text = file_path.read_text()

                if len(artifacts) >= 50:
                    break

        return StateSnapshot(control=control, tasks=tasks, gates=gates, artifacts=artifacts, output=output)
