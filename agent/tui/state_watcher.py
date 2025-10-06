from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _human_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}h {minutes:02d}m {secs:02d}s"
    if minutes:
        return f"{minutes:d}m {secs:02d}s"
    return f"{secs:d}s"


@dataclass
class ControlState:
    status: str = "IDLE"
    provider: str = "--"
    model: str = "--"
    session_duration: str = "0s"
    cycle_count: int = 0
    cycle_status: str = "--"
    available_models: List[str] = field(default_factory=list)


@dataclass
class CycleState:
    cycle_number: str = "cycle_000"
    phase: str = "waiting"
    elapsed: str = "0s"
    estimate: str = "--"
    fastpath: str = "--"


@dataclass
class TaskState:
    identifier: str
    title: str
    status: str


@dataclass
class GateState:
    name: str
    status: str
    summary: str


@dataclass
class ArtifactState:
    label: str
    path: Path
    kind: str


@dataclass
class OutputState:
    diff_text: str = ""
    findings: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    config_text: str = ""


@dataclass
class StateSnapshot:
    control: ControlState
    cycle: CycleState
    tasks: List[TaskState]
    gates: List[GateState]
    artifacts: List[ArtifactState]
    output: OutputState


class StateWatcher:
    """Loads lightweight snapshots of agent state for the TUI."""

    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.state_root = self.repo_root / "state"
        self.artifact_root = self.repo_root / "artifacts"
        self.control_root = self.repo_root / "local" / "control"
        self.config_path = self.repo_root / "config.json"

    def snapshot(self) -> StateSnapshot:
        cycle_dir = self._latest_cycle()
        control = self._load_control_state()
        cycle, diff_text, findings, logs = self._load_cycle_state(cycle_dir)
        tasks = self._load_tasks()
        gates = self._load_gates(cycle_dir)
        artifacts = self._load_artifacts(cycle_dir)
        config_text = self.config_path.read_text(encoding="utf-8") if self.config_path.exists() else "{}"
        output = OutputState(diff_text=diff_text, findings=findings, logs=logs, config_text=config_text)
        return StateSnapshot(
            control=control,
            cycle=cycle,
            tasks=tasks,
            gates=gates,
            artifacts=artifacts,
            output=output,
        )

    # ------------------------------------------------------------------
    # Control panel helpers
    # ------------------------------------------------------------------

    def _load_control_state(self) -> ControlState:
        cfg = _read_json(self.config_path)
        provider_cfg = cfg.get("provider", {})
        provider_name = provider_cfg.get("name") or provider_cfg.get("provider") or provider_cfg.get("type") or "--"
        model_name = provider_cfg.get("model") or provider_cfg.get("model_name") or provider_cfg.get("engine") or "--"
        models = provider_cfg.get("models") or provider_cfg.get("available_models") or []
        if not models and model_name != "--":
            models = [model_name]

        session_meta = _read_json(self.state_root / "session.json")
        status = session_meta.get("status", "idle").upper()
        started_at = session_meta.get("active_started_at")
        elapsed = _human_time(time.time() - started_at) if started_at else "0s"
        cycle_count = int(session_meta.get("cycle_count", 0))
        cycle_status = session_meta.get("active_scope") or "--"

        return ControlState(
            status=status,
            provider=str(provider_name),
            model=str(model_name),
            session_duration=elapsed,
            cycle_count=cycle_count,
            cycle_status=str(cycle_status),
            available_models=[str(m) for m in models],
        )

    # ------------------------------------------------------------------
    # Cycle & output helpers
    # ------------------------------------------------------------------

    def _load_cycle_state(self, cycle_dir: Optional[Path]) -> tuple[CycleState, str, List[Dict[str, Any]], List[str]]:
        diff_text = ""
        findings: List[Dict[str, Any]] = []
        logs: List[str] = []
        cycle_state = CycleState()

        if cycle_dir is None:
            return cycle_state, diff_text, findings, logs

        cycle_state.cycle_number = cycle_dir.name
        meta = _read_json(cycle_dir / "cycle.meta.json")
        production_gate = _read_json(cycle_dir / "production_gate.json")

        if meta:
            cycle_state.phase = meta.get("phase", cycle_state.phase)
            elapsed = meta.get("elapsed_seconds") or meta.get("duration")
            if elapsed is not None:
                cycle_state.elapsed = _human_time(float(elapsed))
            estimate = meta.get("estimated_total_seconds") or meta.get("eta")
            if estimate is not None:
                cycle_state.estimate = _human_time(float(estimate))
            watched = meta.get("fastpath", {})
            if isinstance(watched, dict):
                paths = watched.get("touched_paths") or watched.get("paths") or []
                if paths:
                    cycle_state.fastpath = ", ".join(paths[:3]) + ("…" if len(paths) > 3 else "")
            else:
                value = meta.get("fastpath")
                if isinstance(value, list):
                    paths = value
                    cycle_state.fastpath = ", ".join(map(str, paths[:3])) + ("…" if len(paths) > 3 else "")
                elif isinstance(value, str):
                    cycle_state.fastpath = value

        diff_path_candidates = [
            cycle_dir / "diff.patch",
            cycle_dir / "applied.patch",
            cycle_dir / "proposed.patch",
        ]
        for candidate in diff_path_candidates:
            if candidate.exists():
                try:
                    diff_text = candidate.read_text(encoding="utf-8")
                    break
                except Exception:
                    pass

        findings_path = cycle_dir / "findings.json"
        if findings_path.exists():
            data = _read_json(findings_path)
            if isinstance(data, list):
                findings = data
            elif isinstance(data, dict):
                findings = data.get("findings", []) or data.get("results", []) or []

        if production_gate:
            for analyzer, payload in production_gate.get("results", {}).items():
                gate_findings = payload.get("findings", [])
                for entry in gate_findings:
                    enriched = dict(entry)
                    enriched["analyzer"] = analyzer
                    findings.append(enriched)

        log_path = cycle_dir / "agent.log"
        if not log_path.exists():
            log_path = cycle_dir / "runtime.log"
        if log_path.exists():
            try:
                lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                logs = lines[-400:]
            except Exception:
                logs = []

        return cycle_state, diff_text, findings, logs

    # ------------------------------------------------------------------
    # Tasks & gates
    # ------------------------------------------------------------------

    def _load_tasks(self) -> List[TaskState]:
        tasks: List[TaskState] = []
        scheduler_meta = _read_json(self.state_root / "scheduler.json")
        tasks_meta = _read_json(self.state_root / "tasks.json")
        queue_items: List[Dict[str, Any]] = []

        if scheduler_meta:
            active = scheduler_meta.get("active")
            if isinstance(active, dict):
                queue_items.append(active | {"_active": True})
            for item in scheduler_meta.get("queue", []):
                if isinstance(item, dict):
                    queue_items.append(item)
        elif tasks_meta:
            for item in tasks_meta.get("tasks", []):
                if isinstance(item, dict):
                    queue_items.append(item)

        if not queue_items:
            return tasks

        for index, item in enumerate(queue_items):
            name = item.get("name") or item.get("task") or item.get("id") or f"task-{index+1}"
            status = item.get("status") or ("running" if item.get("_active") else "pending")
            tasks.append(
                TaskState(
                    identifier=str(item.get("id") or name),
                    title=str(name),
                    status=str(status),
                )
            )
        return tasks

    def _load_gates(self, cycle_dir: Optional[Path]) -> List[GateState]:
        gate_states: List[GateState] = []
        if cycle_dir is None:
            return gate_states

        production_gate = _read_json(cycle_dir / "production_gate.json")
        if not production_gate:
            return gate_states

        for analyzer, payload in production_gate.get("results", {}).items():
            status = payload.get("status") or ("passed" if payload.get("ok") else "failed")
            summary = payload.get("summary") or payload.get("message") or ""
            gate_states.append(GateState(name=str(analyzer), status=str(status), summary=str(summary)))
        return gate_states

    # ------------------------------------------------------------------
    # Artifacts
    # ------------------------------------------------------------------

    def _load_artifacts(self, cycle_dir: Optional[Path]) -> List[ArtifactState]:
        artifacts: List[ArtifactState] = []
        if cycle_dir is None:
            return artifacts

        for path in sorted(cycle_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(cycle_dir)
            label = f"{cycle_dir.name}/{rel.as_posix()}"
            kind = self._classify_artifact(path)
            artifacts.append(ArtifactState(label=label, path=path, kind=kind))
        return artifacts

    @staticmethod
    def _classify_artifact(path: Path) -> str:
        name = path.name.lower()
        suffix = path.suffix.lower()
        if name.endswith("diff.patch") or suffix == ".patch":
            return "diff"
        if "finding" in name or suffix in {".json"}:
            return "findings"
        if suffix in {".log", ".txt"}:
            return "log"
        return "artifact"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _latest_cycle(self) -> Optional[Path]:
        if not self.artifact_root.exists():
            return None
        cycle_dirs = [p for p in self.artifact_root.iterdir() if p.is_dir() and p.name.startswith("cycle_")]
        if not cycle_dirs:
            return None
        return sorted(cycle_dirs)[-1]


__all__ = [
    "ControlState",
    "CycleState",
    "TaskState",
    "GateState",
    "ArtifactState",
    "OutputState",
    "StateSnapshot",
    "StateWatcher",
]
