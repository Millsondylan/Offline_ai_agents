from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class Finding:
    id: str
    message: str
    severity: str
    path: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'message': self.message,
            'severity': self.severity,
            'path': self.path,
            'line': self.line,
            'column': self.column,
            'suggestion': self.suggestion,
            'data': self.data,
        }


@dataclass
class CommandResult:
    command: Sequence[str]
    code: int
    output: str
    elapsed: float


@dataclass
class Grade:
    status: str
    summary: str
    findings: List[Finding] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyzerResult:
    name: str
    status: str
    summary: str
    findings: List[Finding]
    suggestions: List[str]
    data: Dict[str, Any]
    artifacts: Dict[str, Any]
    command: Optional[CommandResult] = None

    @property
    def ok(self) -> bool:
        return self.status == 'ok'

    @property
    def skipped(self) -> bool:
        return self.status == 'skipped'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status,
            'summary': self.summary,
            'findings': [f.to_dict() for f in self.findings],
            'suggestions': self.suggestions,
            'data': self.data,
            'artifacts': self.artifacts,
            'command': {
                'cmd': list(self.command.command) if self.command else None,
                'code': self.command.code if self.command else None,
                'output': self.command.output if self.command else None,
                'elapsed': self.command.elapsed if self.command else None,
            }
            if self.command
            else None,
        }


class Analyzer:
    name: str = "base"
    produces_artifact: Optional[str] = None

    def __init__(self, settings: Optional[Dict[str, Any]] = None) -> None:
        self.settings = settings or {}

    def available(self) -> bool:
        return True

    def discover(self, repo_root: str, files: Optional[List[str]]) -> List[str]:
        return files or []

    def execute(self, repo_root: str, cycle_dir: str, targets: List[str]) -> CommandResult:
        raise NotImplementedError

    def parse(
        self,
        repo_root: str,
        cycle_dir: str,
        command: CommandResult,
        targets: List[str],
    ) -> Dict[str, Any]:
        return {"raw": command.output, "code": command.code}

    def grade(
        self,
        repo_root: str,
        cycle_dir: str,
        command: CommandResult,
        parsed: Dict[str, Any],
        targets: List[str],
    ) -> Grade:
        status = "ok" if command.code == 0 else "failed"
        summary = f"exit {command.code}"
        return Grade(status=status, summary=summary, data=parsed)

    def suggest_fixes(
        self,
        repo_root: str,
        cycle_dir: str,
        command: CommandResult,
        parsed: Dict[str, Any],
        grade: Grade,
        targets: List[str],
    ) -> List[str]:
        return []

    def analyze(
        self,
        repo_root: str,
        cycle_dir: str,
        files: Optional[List[str]] = None,
    ) -> AnalyzerResult:
        if not self.available():
            return AnalyzerResult(
                name=self.name,
                status="skipped",
                summary=f"{self.name} not available",
                findings=[],
                suggestions=[],
                data={},
                artifacts={},
            )

        targets = self.discover(repo_root, files)
        command = self.execute(repo_root, cycle_dir, targets)
        parsed = self.parse(repo_root, cycle_dir, command, targets)
        grade = self.grade(repo_root, cycle_dir, command, parsed, targets)
        suggestions = self.suggest_fixes(repo_root, cycle_dir, command, parsed, grade, targets)
        self._persist_artifacts(cycle_dir, grade.artifacts)
        return AnalyzerResult(
            name=self.name,
            status=grade.status,
            summary=grade.summary,
            findings=grade.findings,
            suggestions=suggestions,
            data=grade.data,
            artifacts=grade.artifacts,
            command=command,
        )

    # Helpers --------------------------------------------------------------
    @staticmethod
    def _which(cmd: str) -> bool:
        return shutil.which(cmd) is not None

    @staticmethod
    def _run(cmd: Sequence[str], cwd: Optional[str] = None, timeout: int = 1200) -> CommandResult:
        start = time.time()
        proc = subprocess.run(
            list(cmd),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        out = proc.stdout.decode("utf-8", errors="replace")
        return CommandResult(command=list(cmd), code=proc.returncode, output=out, elapsed=time.time() - start)

    @staticmethod
    def _write_json(path: str | Path, payload: Dict[str, Any]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)

    @staticmethod
    def _write_text(path: str | Path, content: str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

    def _persist_artifacts(self, cycle_dir: str, artifacts: Dict[str, Any]) -> None:
        if not artifacts:
            return
        for filename, payload in artifacts.items():
            path = Path(cycle_dir) / filename
            if isinstance(payload, (dict, list)):
                self._write_json(path, payload)  # type: ignore[arg-type]
            else:
                self._write_text(path, str(payload))


def build_finding(
    *,
    identifier: str,
    message: str,
    severity: str,
    path: Optional[str] = None,
    line: Optional[int] = None,
    column: Optional[int] = None,
    suggestion: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Finding:
    return Finding(
        id=identifier,
        message=message,
        severity=severity,
        path=path,
        line=line,
        column=column,
        suggestion=suggestion,
        data=data or {},
    )
