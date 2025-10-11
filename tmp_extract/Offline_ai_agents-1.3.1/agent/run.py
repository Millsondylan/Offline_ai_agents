from __future__ import annotations

import json
import os
import queue
import shlex
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .analyzers import (
    AxeAnalyzer,
    BanditAnalyzer,
    LighthouseAnalyzer,
    PipAuditAnalyzer,
    PytestCoverageAnalyzer,
    RepoHygieneAnalyzer,
    RuffAnalyzer,
    SemgrepAnalyzer,
)
from .analyzers.base import AnalyzerResult, Finding
from .patcher import apply_patch_with_git, extract_unified_diff
from .providers import KeyStore, ProviderError, provider_from_config
from .thinking_logger import ThinkingLogger
from .utils import collect_artifacts, ensure_dir, now_ts, read_text, run_cmd, write_text

try:  # Optional watchdog support
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except Exception:  # pragma: no cover - optional dependency
    FileSystemEventHandler = object  # type: ignore
    Observer = None  # type: ignore


ARTIFACT_ROOT = Path(__file__).resolve().parent / "artifacts"
STATE_ROOT = Path(__file__).resolve().parent / "state"
LOCAL_ROOT = Path(__file__).resolve().parent / "local"


@dataclass
class GateReport:
    allow: bool
    rationale: List[str]
    results: Dict[str, AnalyzerResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allow": self.allow,
            "rationale": self.rationale,
            "results": {k: v.to_dict() for k, v in self.results.items()},
        }


@dataclass
class CommitState:
    auto_commit: bool
    cadence_seconds: int
    last_commit_at: float = 0.0
    force_next: bool = False

    def should_commit(self, now: float) -> bool:
        if self.force_next:
            return True
        if not self.auto_commit:
            return False
        if self.last_commit_at <= 0:
            return True
        return (now - self.last_commit_at) >= self.cadence_seconds

    def record_commit(self, timestamp: float) -> None:
        self.last_commit_at = timestamp
        self.force_next = False

    def schedule_now(self) -> None:
        self.force_next = True

    def toggle(self, enabled: bool) -> None:
        self.auto_commit = enabled

    def next_commit_at(self) -> Optional[float]:
        if not self.auto_commit:
            return None
        if self.last_commit_at <= 0:
            return time.time()
        return self.last_commit_at + self.cadence_seconds

    def to_meta(self) -> Dict[str, Any]:
        return {
            "auto_commit": self.auto_commit,
            "cadence_seconds": self.cadence_seconds,
            "last_commit_at": self.last_commit_at,
            "force_next": self.force_next,
            "next_commit_at": self.next_commit_at(),
        }


@dataclass
class SessionState:
    enabled: bool
    default_duration: int
    default_post_review_delay: int
    max_duration: int
    active_scope: Optional[str] = None
    active_started_at: Optional[float] = None
    active_duration: Optional[int] = None
    review_eta: Optional[float] = None
    last_review_at: Optional[float] = None
    status: str = "idle"

    def start(self, scope: str, duration: Optional[int], review_delay: Optional[int]) -> None:
        if not self.enabled:
            return
        dur = duration or self.default_duration
        if dur > self.max_duration:
            dur = self.max_duration
        self.active_scope = scope
        self.active_duration = dur
        self.active_started_at = time.time()
        delay = review_delay if review_delay is not None else self.default_post_review_delay
        self.review_eta = None if delay <= 0 else self.active_started_at + dur + delay
        self.status = "running"

    def stop(self) -> None:
        self.active_scope = None
        self.active_started_at = None
        self.active_duration = None
        self.status = "idle"

    def tick(self) -> None:
        if not self.enabled or self.active_scope is None or self.active_started_at is None:
            return
        if self.active_duration is None:
            return
        if time.time() >= self.active_started_at + self.active_duration:
            self.status = "awaiting_review"
            if self.review_eta is None:
                self.review_eta = time.time()

    def review_due(self) -> bool:
        if not self.enabled:
            return False
        if self.review_eta is None:
            return False
        return time.time() >= self.review_eta

    def record_review(self) -> None:
        self.last_review_at = time.time()
        self.review_eta = None
        self.stop()

    def to_meta(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "status": self.status,
            "active_scope": self.active_scope,
            "active_started_at": self.active_started_at,
            "active_duration": self.active_duration,
            "review_eta": self.review_eta,
            "last_review_at": self.last_review_at,
        }


class FastPathMonitor:
    """Watch filesystem changes and expose touched paths for fast checks."""

    def __init__(self, repo_root: Path, enabled: bool) -> None:
        self.repo_root = repo_root
        self.enabled = enabled and Observer is not None
        self._queue: "queue.Queue[Path]" = queue.Queue()
        self._observer: Optional[Observer] = None  # type: ignore[type-arg]
        if self.enabled:
            handler = self._make_handler()
            self._observer = Observer()
            self._observer.schedule(handler, str(repo_root), recursive=True)
            self._observer.daemon = True
            self._observer.start()

    def _make_handler(self):  # pragma: no cover - glue code
        monitor = self

        class Handler(FileSystemEventHandler):  # type: ignore[misc]
            def on_modified(self, event):
                if getattr(event, "is_directory", False):
                    return
                monitor._queue.put(Path(event.src_path))

            def on_created(self, event):
                if getattr(event, "is_directory", False):
                    return
                monitor._queue.put(Path(event.src_path))

        return Handler()

    def drain(self) -> List[Path]:
        paths: List[Path] = []
        if not self.enabled:
            return paths
        try:
            while True:
                paths.append(self._queue.get_nowait())
        except queue.Empty:
            pass
        return paths

    def stop(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)


def load_config(cfg_path: Path) -> Dict[str, Any]:
    with open(cfg_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def cfg_get(cfg: Dict[str, Any], path: str, default: Any = None) -> Any:
    parts = path.split(".")
    cursor: Any = cfg
    for part in parts:
        if isinstance(cursor, dict) and part in cursor:
            cursor = cursor[part]
        else:
            return default
    return cursor


def merge_defaults(cfg: Dict[str, Any]) -> Dict[str, Any]:
    merged = cfg.copy()
    merged.setdefault("loop", {})
    merged.setdefault("git", {})
    merged.setdefault("sessions", {})
    merged.setdefault("commands", {})
    merged.setdefault("gate", {})
    merged.setdefault("ui_audits", {})
    merged.setdefault("tui", {})
    return merged

def load_commit_state(cfg: Dict[str, Any], state_root: Path = None) -> CommitState:
    if state_root is None:
        state_root = STATE_ROOT
    ensure_dir(str(state_root))
    path = state_root / "commit_scheduler.json"
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return CommitState(
                auto_commit=bool(payload.get("auto_commit", True)),
                cadence_seconds=int(payload.get("cadence_seconds", cfg_get(cfg, "git.commit_cadence_seconds", 3600))),
                last_commit_at=float(payload.get("last_commit_at", 0.0)),
                force_next=bool(payload.get("force_next", False)),
            )
        except Exception:
            pass
    return CommitState(
        auto_commit=bool(cfg_get(cfg, "git.auto_commit", True)),
        cadence_seconds=int(cfg_get(cfg, "git.commit_cadence_seconds", 3600)),
    )


def save_commit_state(state: CommitState, state_root: Path = None) -> None:
    if state_root is None:
        state_root = STATE_ROOT
    ensure_dir(str(state_root))
    path = state_root / "commit_scheduler.json"
    path.write_text(json.dumps(state.to_meta(), indent=2), encoding="utf-8")


def load_session_state(cfg: Dict[str, Any], state_root: Path = None) -> SessionState:
    if state_root is None:
        state_root = STATE_ROOT
    ensure_dir(str(state_root))
    path = state_root / "session.json"
    defaults = SessionState(
        enabled=bool(cfg_get(cfg, "sessions.enabled", True)),
        default_duration=int(cfg_get(cfg, "sessions.default_duration_seconds", 3600)),
        default_post_review_delay=int(cfg_get(cfg, "sessions.default_post_review_delay_seconds", 3600)),
        max_duration=int(cfg_get(cfg, "sessions.max_duration_seconds", 28800)),
    )
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            defaults.status = payload.get("status", defaults.status)
            defaults.active_scope = payload.get("active_scope")
            defaults.active_started_at = payload.get("active_started_at")
            defaults.active_duration = payload.get("active_duration")
            defaults.review_eta = payload.get("review_eta")
            defaults.last_review_at = payload.get("last_review_at")
        except Exception:
            pass
    return defaults


def save_session_state(state: SessionState, state_root: Path = None) -> None:
    if state_root is None:
        state_root = STATE_ROOT
    ensure_dir(str(state_root))
    path = state_root / "session.json"
    path.write_text(json.dumps(state.to_meta(), indent=2), encoding="utf-8")


def serialize_findings(findings: Iterable[Finding]) -> List[Dict[str, Any]]:
    return [f.to_dict() for f in findings]

def run_production_gate(
    repo_root: Path,
    cfg: Dict[str, Any],
    cycle_dir: Path,
    proposed_files: Optional[List[str]] = None,
) -> GateReport:
    gate_cfg = cfg_get(cfg, "gate", {}) or {}
    ui_cfg = cfg_get(cfg, "ui_audits", {}) or {}
    analyzers = [
        RuffAnalyzer({"respect_noqa": gate_cfg.get("respect_noqa", False)}),
        PytestCoverageAnalyzer({"timeout": cfg_get(cfg, "commands.test.timeout", 3600)}),
        BanditAnalyzer(),
        SemgrepAnalyzer({"rules": gate_cfg.get("semgrep_rules", [])}),
        PipAuditAnalyzer({"fix": gate_cfg.get("pip_audit_fix", False)}),
        RepoHygieneAnalyzer(),
    ]
    if ui_cfg.get("enabled"):
        targets = ui_cfg.get("targets", [])
        analyzers.extend(
            [
                LighthouseAnalyzer({"targets": targets, "flags": ui_cfg.get("lighthouse", {}).get("flags", [])}),
                AxeAnalyzer({"targets": targets, "flags": ui_cfg.get("axe", {}).get("flags", [])}),
                Pa11yAnalyzer({"targets": targets, "flags": ui_cfg.get("pa11y", {}).get("flags", [])}),
            ]
        )

    results: Dict[str, AnalyzerResult] = {}
    for analyzer in analyzers:
        try:
            res = analyzer.analyze(str(repo_root), str(cycle_dir), files=proposed_files)
        except Exception as exc:  # pragma: no cover - runtime guard
            summary = f"exception: {exc}"
            res = AnalyzerResult(
                name=analyzer.name,
                status="error",
                summary=summary,
                findings=[],
                suggestions=[],
                data={"error": str(exc)},
                artifacts={},
            )
        results[analyzer.name] = res

    allow, rationale = evaluate_gate(results, gate_cfg, ui_cfg)
    gate = GateReport(allow=allow, rationale=rationale, results=results)
    write_text(str(cycle_dir / "production_gate.json"), json.dumps(gate.to_dict(), indent=2))
    return gate


def evaluate_gate(
    results: Dict[str, AnalyzerResult],
    gate_cfg: Dict[str, Any],
    ui_cfg: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    allow = True
    rationale: List[str] = []

    def finding_count(name: str, severities: Sequence[str]) -> int:
        res = results.get(name)
        if not res:
            return 0
        wanted = {s.lower() for s in severities}
        return sum(1 for f in res.findings if f.severity.lower() in wanted)

    # Lint gate
    ruff_res = results.get("ruff")
    if ruff_res and not ruff_res.ok:
        allow = False
        rationale.append("ruff reported style issues")

    # Tests + coverage gate
    pytest_res = results.get("pytest_cov")
    if pytest_res:
        if pytest_res.status != "ok":
            allow = False
            rationale.append("pytest failed")
        else:
            coverage_threshold = float(gate_cfg.get("min_coverage", 0.0))
            cov_pct = extract_coverage_percentage(pytest_res.data)
            if cov_pct is not None and cov_pct < coverage_threshold:
                allow = False
                rationale.append(f"coverage {cov_pct:.2f} below threshold {coverage_threshold:.2f}")

    # Security code gate
    bandit_fail_levels = gate_cfg.get("bandit_fail_levels", ["HIGH", "CRITICAL"])
    if finding_count("bandit", bandit_fail_levels) > 0:
        allow = False
        rationale.append("bandit high/critical issues present")
    if finding_count("semgrep", ["high", "critical"]) > 0:
        allow = False
        rationale.append("semgrep high/critical issues present")

    # Dependency gate
    if finding_count("pip_audit", ["high", "critical"]) > 0:
        allow = False
        rationale.append("pip-audit high/critical vulnerabilities present")

    # UI audits gate (optional)
    if ui_cfg.get("enabled"):
        for name in ("axe", "pa11y", "lighthouse"):
            if finding_count(name, ["critical"]) > 0:
                allow = False
                rationale.append(f"{name} critical accessibility findings")

    if not allow and gate_cfg.get("allow_override"):
        rationale.append("gate override enabled; proceeding despite failures")
        allow = True

    return allow, rationale


def extract_coverage_percentage(data: Dict[str, Any]) -> Optional[float]:
    coverage = data.get("coverage") if isinstance(data, dict) else None
    if isinstance(coverage, dict):
        totals = coverage.get("totals")
        if isinstance(totals, dict):
            pct = totals.get("percent_covered")
            if isinstance(pct, (int, float)):
                return float(pct) / 100.0 if pct > 1 else float(pct)
    return None

def parse_files_from_diff(patch_text: Optional[str]) -> List[str]:
    files: List[str] = []
    if not patch_text:
        return files
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.strip().split()
            if len(parts) >= 4:
                path = parts[2]
                if path.startswith("a/"):
                    path = path[2:]
                files.append(path)
    seen = set()
    ordered: List[str] = []
    for path in files:
        if path not in seen:
            ordered.append(path)
            seen.add(path)
    return ordered


def build_commit_message(repo_root: Path, proposed_files: List[str], patch_text: str) -> str:
    run_cmd("git add -A")
    _, stat_out = run_cmd("git diff --cached --shortstat")
    summary = (stat_out or "").strip()
    if not summary:
        if proposed_files:
            base = [Path(p).name for p in proposed_files[:3]]
            if len(proposed_files) > 3:
                summary = f"update {', '.join(base)}, +{len(proposed_files) - 3} more"
            else:
                summary = f"update {', '.join(base)}"
        else:
            summary = "apply patch"
    return f"agent edits: {summary}\n"


def subprocess_with_env(args: Sequence[str], cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
    import subprocess

    proc = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return proc.returncode, proc.stdout.decode("utf-8", errors="replace")


def commit_with_temp_index(
    repo_root: Path,
    branch: Optional[str],
    message: str,
    proposed_files: List[str],
    cycle_dir: Path,
) -> Tuple[bool, Dict[str, Any]]:
    meta: Dict[str, Any] = {}
    tmp_index = cycle_dir / "_tmp_index"
    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = str(tmp_index)

    code, out = subprocess_with_env(["git", "rev-parse", "HEAD"], cwd=str(repo_root), env=env)
    if code != 0:
        meta["error"] = "rev-parse HEAD failed"
        write_text(str(cycle_dir / "commit.meta.json"), json.dumps(meta, indent=2))
        return False, meta
    head = (out or "").strip().splitlines()[-1]

    if branch:
        run_cmd(f"git rev-parse --verify {branch} >/dev/null 2>&1 || git checkout -B {branch}")
        run_cmd(f"git checkout {branch}")

    code, out = subprocess_with_env(["git", "read-tree", head], cwd=str(repo_root), env=env)
    meta["read-tree"] = {"code": code, "out": out}
    if code != 0:
        write_text(str(cycle_dir / "commit.meta.json"), json.dumps(meta, indent=2))
        return False, meta

    for path in proposed_files:
        subprocess_with_env(["git", "add", "--", path], cwd=str(repo_root), env=env)
    code, out = subprocess_with_env(["git", "diff", "--cached", "--name-only"], cwd=str(repo_root), env=env)
    staged = [ln.strip() for ln in (out or "").splitlines() if ln.strip()]
    meta["staged"] = staged
    meta["proposed_files"] = proposed_files
    extras = [p for p in staged if p not in proposed_files]
    if extras:
        meta["error"] = "staged files outside proposed patch"
        write_text(str(cycle_dir / "commit.meta.json"), json.dumps(meta, indent=2))
        return False, meta

    code, out = subprocess_with_env(["git", "write-tree"], cwd=str(repo_root), env=env)
    tree_oid = (out or "").strip().splitlines()[-1] if code == 0 else None
    meta["write-tree"] = {"code": code, "tree": tree_oid}
    if code != 0 or not tree_oid:
        write_text(str(cycle_dir / "commit.meta.json"), json.dumps(meta, indent=2))
        return False, meta

    code, out = subprocess_with_env(["git", "commit-tree", "-p", head, "-m", message, tree_oid], cwd=str(repo_root), env=env)
    commit_oid = (out or "").strip().splitlines()[-1] if code == 0 else None
    meta["commit-tree"] = {"code": code, "commit": commit_oid}
    write_text(str(cycle_dir / "commit.meta.json"), json.dumps(meta, indent=2))
    if code != 0 or not commit_oid:
        return False, meta

    ref = f"refs/heads/{branch}" if branch else "HEAD"
    code, out = subprocess_with_env(["git", "update-ref", ref, commit_oid, head], cwd=str(repo_root), env=env)
    meta["update-ref"] = {"code": code, "out": out, "ref": ref, "old": head, "new": commit_oid}
    write_text(str(cycle_dir / "update_ref.meta.json"), json.dumps(meta["update-ref"], indent=2))
    if code != 0:
        return False, meta

    return True, meta

def run_custom_command(name: str, cfg: Dict[str, Any], cycle_dir: Path) -> Dict[str, Any]:
    section = cfg_get(cfg, f"commands.{name}", {}) or {}
    enabled = bool(section.get("enabled", False))
    result = {"enabled": enabled, "code": None, "output": ""}
    if not enabled:
        return result
    cmd = section.get("cmd")
    if not cmd:
        result["output"] = "command not configured"
        return result
    timeout = int(section.get("timeout") or section.get("timeout_seconds") or 600)
    code, out = run_cmd(cmd, timeout=timeout)
    result.update({"code": code, "output": out})
    log_path = cycle_dir / f"{name}.log"
    write_text(str(log_path), out)
    if name == "screenshots":
        glob_pattern = section.get("collect_glob")
        if glob_pattern:
            shots_dir = cycle_dir / "screenshots"
            count = collect_artifacts(glob_pattern, str(shots_dir))
            write_text(str(shots_dir / "_COLLECTION.txt"), f"collected={count} from {glob_pattern}\n")
    return result

def compose_prompt(
    repo_root: Path,
    cycle_dir: Path,
    command_results: Dict[str, Dict[str, Any]],
    session: SessionState,
    scheduler: CommitState,
    scope_hint: Optional[str],
    fast_targets: Optional[Sequence[Path]] = None,
) -> str:
    sections: List[str] = []
    sections.append("Agent Cycle Prompt\n")

    code, out = run_cmd(
        "git status --porcelain=v1 && echo --- && git rev-parse --abbrev-ref HEAD && echo --- && git log -1 --oneline",
        timeout=15,
    )
    sections.append("[git]\n" + out.strip() + "\n")

    for name, result in command_results.items():
        sections.append(f"[command:{name}] enabled={result.get('enabled')} exit={result.get('code')}\n")
        output = (result.get("output") or "").strip()
        if output:
            sections.append(output[:20000] + ("\n" if not output.endswith("\n") else ""))

    if fast_targets:
        rels: List[str] = []
        for fp in fast_targets:
            try:
                rels.append(str(Path(fp).relative_to(repo_root)))
            except ValueError:
                rels.append(str(fp))
        sections.append("[fast_path]\n" + "\n".join(rels))

    if session.enabled and session.active_scope:
        sections.append(
            "[session]\n"
            f"scope={session.active_scope}\nstatus={session.status}\n"
        )
    schedule_line = f"auto_commit={'on' if scheduler.auto_commit else 'off'} cadence={scheduler.cadence_seconds}s"
    sections.append("[commit_policy]\n" + schedule_line + "\n")

    if scope_hint:
        sections.append(f"[scope_hint]\nLimit changes to: {scope_hint}\n")

    # Check for user-provided task
    task_file = repo_root / "agent" / "local" / "control" / "task.txt"
    user_task = None
    if task_file.exists():
        try:
            user_task = task_file.read_text(encoding="utf-8").strip()
        except Exception:
            pass

    sections.append("Task:\n")
    if user_task:
        sections.append(f"USER TASK (PRIORITY): {user_task}\n\n")
        sections.append(
            "Complete the user's task above. Review ALL context (git status, test results, linter output, prior commands)"
            " and propose the safest patch that accomplishes the task.\n\n"
        )
    else:
        sections.append(
            "You are an offline-first autonomous engineer operating on this repository."
            " Review ALL context above (git status, test results, linter output, prior commands, session scope)"
            " and propose the safest patch that progresses the current goals.\n\n"
        )
    sections.append(
        "Guidelines:\n"
        "- Keep changes minimal, compilable, and focused on the scope\n"
        "- Address any failing tests or linter errors shown above\n"
        "- Make thoughtful, deliberate changes - explain your reasoning\n"
        "- Consider edge cases and error handling\n"
        "- Ensure backward compatibility where applicable\n"
        "- Follow the codebase's existing patterns and style\n"
        "- Add tests for new functionality\n"
        "- Update documentation if interfaces change\n\n"
        "Your changes will go through comprehensive verification:\n"
        "- Syntax validation\n"
        "- Test suite execution\n"
        "- Security scanning\n"
        "- Linting and type checking\n"
        "- Code coverage analysis\n\n"
        "Think through your approach before generating the diff."
    )
    sections.append("\nOutput format:\n")
    sections.append("Return ONLY a unified diff fenced with ```diff ...```. Include full file contents for new files.\n"
                   "The diff should be production-ready and pass all quality gates.")
    prompt = "\n".join(sections)
    write_text(str(cycle_dir / "prompt.md"), prompt)
    return prompt

def run_fast_checks(repo_root: Path, fast_paths: List[Path], cycle_dir: Path) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"paths": [str(p) for p in fast_paths], "ruff_fix": None, "pytest": None}
    if not fast_paths:
        return summary
    py_files = [str(p.relative_to(repo_root)) for p in fast_paths if p.suffix == ".py" and p.is_file()]
    if py_files and shutil.which("ruff"):
        cmd = ["ruff", "check", "--fix-only", *py_files]
        shell_cmd = " ".join(shlex.quote(part) for part in cmd)
        code, out = run_cmd(shell_cmd)
        summary["ruff_fix"] = {"code": code, "output": out[:2000]}
        write_text(str(cycle_dir / "fast_path_ruff.log"), out)
    test_targets = [p for p in py_files if "test" in p]
    if test_targets and shutil.which("pytest"):
        cmd = ["pytest", "-q", *test_targets]
        shell_cmd = " ".join(shlex.quote(part) for part in cmd)
        code, out = run_cmd(shell_cmd)
        summary["pytest"] = {"code": code, "output": out[:2000]}
        write_text(str(cycle_dir / "fast_path_pytest.log"), out)
    write_text(str(cycle_dir / "fast_path.meta.json"), json.dumps(summary, indent=2))
    return summary

def process_control_commands(scheduler: CommitState, session: SessionState, repo_root: Path) -> None:
    control_dir = repo_root / "agent" / "local" / "control"
    if not control_dir.exists():
        return

    keystore = KeyStore()
    config_path = repo_root / 'agent' / 'config.json'

    def _parse_duration(raw: str) -> Optional[int]:
        raw = raw.strip().lower()
        try:
            if raw.endswith('h'):
                return int(float(raw[:-1]) * 3600)
            if raw.endswith('m'):
                return int(float(raw[:-1]) * 60)
            if raw.endswith('s'):
                return int(float(raw[:-1]))
            return int(float(raw))
        except ValueError:
            return None
    for cmd_file in control_dir.glob("*.cmd"):
        try:
            content = cmd_file.read_text(encoding="utf-8").strip()
        except Exception:
            content = ""
        name = cmd_file.stem.lower()
        if name == "commit_now":
            scheduler.schedule_now()
        elif name == "auto_commit":
            scheduler.toggle(content.lower() != "off")
        elif name == "cadence":
            try:
                scheduler.cadence_seconds = max(60, int(content))
            except ValueError:
                pass
        elif name == "session":
            parts = content.split()
            if parts and parts[0] == "start":
                scope = "repo"
                duration = None
                review = None
                for token in parts[1:]:
                    if token.startswith("scope="):
                        scope = token.split("=", 1)[1]
                    elif token.startswith("dur="):
                        duration = _parse_duration(token.split("=", 1)[1])
                    elif token.startswith("review="):
                        review = _parse_duration(token.split("=", 1)[1])
                session.start(scope, duration, review)
            elif parts and parts[0] == "stop":
                session.stop()
        elif name == "model":
            cfg = load_config(config_path)
            provider_cfg = cfg.setdefault("provider", {})
            provider_cfg["model"] = content or provider_cfg.get("model")
            config_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        elif name == "apikey":
            tokens = content.split()
            if tokens:
                action = tokens[0]
                key_id = tokens[1] if len(tokens) > 1 else None
                value = tokens[2] if len(tokens) > 2 else None
                if action == "set" and key_id and value:
                    keystore.set(key_id, value)
                elif action == "clear" and key_id:
                    keystore.clear(key_id)

        cmd_file.unlink(missing_ok=True)

class AgentLoop:
    def __init__(self, repo_root: Path, cfg: Dict[str, Any]) -> None:
        self.repo_root = repo_root
        self.cfg = merge_defaults(cfg)
        self.loop_cfg = self.cfg.get("loop", {})

        # Use repo_root-based paths instead of hardcoded package paths
        self.artifact_root = self.repo_root / "agent" / "artifacts"
        self.local_root = self.repo_root / "agent" / "local"
        self.state_root = self.repo_root / "agent" / "state"

        provider_cfg = self.cfg.get("provider", {})
        self.provider = provider_from_config(provider_cfg)
        self.commit_state = load_commit_state(self.cfg, self.state_root)
        self.session_state = load_session_state(self.cfg, self.state_root)
        fast_path_enabled = bool(cfg_get(self.loop_cfg, "fast_path_on_fs_change", True))
        self.fast_path = FastPathMonitor(self.repo_root, fast_path_enabled)
        self.max_cycles = int(os.getenv("AGENT_MAX_CYCLES", cfg_get(self.loop_cfg, "max_cycles", 0)))
        self.cooldown = int(os.getenv("AGENT_COOLDOWN_SECONDS", cfg_get(self.loop_cfg, "cooldown_seconds", 120)))
        self.apply_patches = bool(cfg_get(self.loop_cfg, "apply_patches", True))
        self.require_approval = bool(cfg_get(self.loop_cfg, "require_manual_approval", False))
        self.path_prefix = cfg_get(self.cfg, "patch.path_prefix", "") or ""
        git_cfg = self.cfg.get("git", {})
        self.git_commit_enabled = bool(git_cfg.get("commit", True))
        self.git_branch = git_cfg.get("branch")
        self.git_push = bool(git_cfg.get("push", False))
        self.git_remote = git_cfg.get("remote", "origin")
        self.push_interval = int(git_cfg.get("push_interval_seconds", 900))
        cadence = int(git_cfg.get("commit_cadence_seconds", self.commit_state.cadence_seconds))
        self.commit_state.cadence_seconds = cadence
        self.last_push_at = 0.0

        ensure_dir(str(self.artifact_root))
        ensure_dir(str(self.local_root))
        ensure_dir(str(self.local_root / 'control'))
        ensure_dir(str(self.state_root))

        # Initialize thinking logger
        self.thinking_logger = ThinkingLogger(self.state_root)

    def run(self) -> None:
        cycle = 1
        try:
            while True:
                if self.max_cycles and cycle > self.max_cycles:
                    self.thinking_logger.log_thinking("completion", f"Reached max cycles ({self.max_cycles})")
                    break

                # Start new cycle
                self.thinking_logger.start_cycle(cycle)
                self.thinking_logger.log_thinking("planning", f"Beginning cycle {cycle}", {
                    "max_cycles": self.max_cycles,
                    "cooldown": self.cooldown
                })

                process_control_commands(self.commit_state, self.session_state, self.repo_root)
                cfg_snapshot = load_config(self.repo_root / 'agent' / 'config.json')
                self.cfg = merge_defaults(cfg_snapshot)
                desired_model = cfg_snapshot.get('provider', {}).get('model')
                if desired_model and hasattr(self.provider, 'set_model'):
                    try:
                        self.thinking_logger.log_action("switch_model", f"Switching to model: {desired_model}", "started")
                        self.provider.set_model(desired_model)
                        self.thinking_logger.log_action("switch_model", f"Model switched to: {desired_model}", "completed")
                    except Exception as e:
                        self.thinking_logger.log_error("model_switch", f"Failed to switch model: {e}")
                cycle_dir = self.artifact_root / f"cycle_{cycle:03d}_{now_ts()}"
                ensure_dir(str(cycle_dir))

                self.session_state.tick()
                save_session_state(self.session_state, self.state_root)
                write_text(str(cycle_dir / "session.meta.json"), json.dumps(self.session_state.to_meta(), indent=2))

                fast_paths = self.fast_path.drain()
                if fast_paths:
                    self.thinking_logger.log_thinking("analysis", f"Detected {len(fast_paths)} changed files", {
                        "files": [str(p) for p in fast_paths[:5]]  # Log first 5
                    })
                fast_summary = run_fast_checks(self.repo_root, fast_paths, cycle_dir) if fast_paths else {}

                self.thinking_logger.log_thinking("planning", "Running analysis commands")
                command_results: Dict[str, Dict[str, Any]] = {}
                for name in ["analyze", "test", "e2e", "screenshots"]:
                    self.thinking_logger.log_action(f"run_{name}", f"Executing {name} command", "started")
                    command_results[name] = run_custom_command(name, self.cfg, cycle_dir)
                    status = "completed" if command_results[name].get("code") == 0 else "failed"
                    self.thinking_logger.log_action(f"run_{name}", f"{name} command finished", status)

                scope_hint = self.session_state.active_scope
                if scope_hint:
                    self.thinking_logger.log_thinking("strategy", f"Limiting scope to: {scope_hint}")

                self.thinking_logger.log_thinking("planning", "Composing prompt for model")
                prompt = compose_prompt(
                    self.repo_root,
                    cycle_dir,
                    command_results,
                    self.session_state,
                    self.commit_state,
                    scope_hint,
                    fast_paths,
                )

                self.thinking_logger.log_model_interaction(
                    f"Prompt composed ({len(prompt)} chars)",
                    "Awaiting model response...",
                    len(prompt) // 4,  # Rough token estimate
                    None
                )

                try:
                    self.thinking_logger.log_action("generate_patch", "Requesting patch from model", "started")
                    raw = self.provider.generate_patch(prompt, str(cycle_dir))
                    self.thinking_logger.log_action("generate_patch", "Received model response", "completed")
                    if raw:
                        self.thinking_logger.log_model_interaction(
                            f"Prompt sent ({len(prompt)} chars)",
                            f"Response received ({len(raw)} chars)",
                            len(prompt) // 4,
                            len(raw) // 4
                        )
                except ProviderError as exc:
                    self.thinking_logger.log_error("provider", f"Provider error: {exc}")
                    write_text(str(cycle_dir / "provider.error.txt"), str(exc))
                    raw = None

                patch_text = extract_unified_diff(raw) if raw else None
                if raw and not patch_text:
                    self.thinking_logger.log_thinking("analysis", "Model response did not contain a valid diff patch")
                    write_text(str(cycle_dir / "provider_output_no_patch.txt"), raw)
                elif patch_text:
                    self.thinking_logger.log_thinking("decision", "Extracted patch with changes", {
                        "patch_size": len(patch_text)
                    })

                proposed_files = parse_files_from_diff(patch_text)
                if proposed_files:
                    self.thinking_logger.log_code_generation(
                        ", ".join(proposed_files[:3]) + ("..." if len(proposed_files) > 3 else ""),
                        "modify" if patch_text else "none",
                        len(patch_text.splitlines()) if patch_text else 0
                    )

                applied = False
                gate_report: Optional[GateReport] = None
                commit_meta: Dict[str, Any] = {}
                if self.apply_patches and patch_text:
                    if self.require_approval:
                        self.thinking_logger.log_thinking("decision", "Awaiting manual approval before applying patch")
                        approve_path = cycle_dir / "approve.txt"
                        if read_text(str(approve_path)) is None:
                            write_text(str(approve_path), "Put 'ok' to apply this cycle's patch\n")
                        approved = (read_text(str(approve_path)) or "").strip().lower() == "ok"
                    else:
                        approved = True
                    if approved:
                        self.thinking_logger.log_action("apply_patch", f"Applying patch to {len(proposed_files)} files", "started")
                        apply_out = apply_patch_with_git(str(self.repo_root), patch_text, str(cycle_dir), path_prefix=self.path_prefix)
                        write_text(str(cycle_dir / "apply_patch.log"), apply_out)
                        write_text(str(cycle_dir / "applied.patch"), patch_text)
                        applied = True
                        self.thinking_logger.log_action("apply_patch", "Patch applied successfully", "completed")

                        self.thinking_logger.log_thinking("verification", "Running production quality gates")
                        gate_report = run_production_gate(self.repo_root, self.cfg, cycle_dir, proposed_files)

                        # Log gate results
                        if gate_report:
                            for analyzer_name, result in gate_report.results.items():
                                self.thinking_logger.log_verification(
                                    analyzer_name,
                                    result.ok,
                                    result.summary
                                )

                        commit_meta = self._maybe_commit(gate_report, proposed_files, patch_text, cycle_dir)
                    else:
                        self.thinking_logger.log_thinking("decision", "Patch not approved, skipping application")
                        write_text(str(cycle_dir / "apply_patch.log"), "SKIPPED (awaiting approval)")
                else:
                    if patch_text:
                        self.thinking_logger.log_thinking("decision", "Patch generation disabled in config")
                        write_text(str(cycle_dir / "apply_patch.log"), "SKIPPED (apply_patches disabled)")

                # Session post-review gate even without new patch
                if self.session_state.review_due():
                    gate_report = run_production_gate(self.repo_root, self.cfg, cycle_dir, proposed_files or [])
                    self.session_state.record_review()
                    save_session_state(self.session_state, self.state_root)
                    write_text(str(cycle_dir / "session.meta.json"), json.dumps(self.session_state.to_meta(), indent=2))

                meta = {
                    "timestamp": now_ts(),
                    "cycle": cycle,
                    "patch_present": bool(patch_text),
                    "applied": applied,
                    "proposed_files": proposed_files,
                    "gate": gate_report.to_dict() if gate_report else None,
                    "commit": commit_meta,
                    "fast_path": fast_summary,
                }
                write_text(str(cycle_dir / "cycle.meta.json"), json.dumps(meta, indent=2))

                save_commit_state(self.commit_state, self.state_root)
                write_text(str(cycle_dir / "commit_scheduler.meta.json"), json.dumps(self.commit_state.to_meta(), indent=2))

                cycle += 1
                time.sleep(self.cooldown)
        finally:
            self.fast_path.stop()

    def _maybe_commit(
        self,
        gate_report: GateReport,
        proposed_files: List[str],
        patch_text: str,
        cycle_dir: Path,
    ) -> Dict[str, Any]:
        meta: Dict[str, Any] = {"attempted": False, "performed": False}
        if not gate_report.allow:
            meta["reason"] = "gate blocked"
            return meta
        if not self.git_commit_enabled:
            meta["reason"] = "git commits disabled"
            return meta
        now = time.time()
        if not self.commit_state.should_commit(now):
            meta["reason"] = "awaiting cadence"
            return meta
        meta["attempted"] = True
        message = build_commit_message(self.repo_root, proposed_files, patch_text)
        ok, commit_data = commit_with_temp_index(self.repo_root, self.git_branch, message.strip(), proposed_files, cycle_dir)
        meta.update(commit_data)
        meta["message"] = message.strip()
        if ok:
            meta["performed"] = True
            self.commit_state.record_commit(now)
            if self.git_push and message.startswith("agent edits:"):
                if now - self.last_push_at >= self.push_interval:
                    code, out = run_cmd(f"git push {self.git_remote} {self.git_branch or ''}".strip())
                    write_text(str(cycle_dir / "git_push.log"), out)
                    meta["push"] = {"code": code, "remote": self.git_remote, "branch": self.git_branch}
                    if code == 0:
                        self.last_push_at = now
        else:
            meta["error"] = "commit failed"
        return meta

def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    cfg_path = repo_root / "agent" / "config.json"
    cfg = load_config(cfg_path)
    loop = AgentLoop(repo_root, cfg)
    loop.run()


if __name__ == "__main__":
    main()
