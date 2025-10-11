from __future__ import annotations

import json
from typing import Any, Dict, List

from .base import Analyzer, CommandResult, Grade, build_finding


class RuffAnalyzer(Analyzer):
    name = "ruff"

    def available(self) -> bool:
        return self._which("ruff")

    def execute(self, repo_root: str, cycle_dir: str, targets: List[str]) -> CommandResult:
        args = ["ruff", "check", "--output-format", "json"]
        if self.settings.get("respect_noqa"):
            args.append("--respect-noqa")
        args.extend(targets or ["."])
        timeout = int(self.settings.get("timeout", 600))
        return self._run(args, cwd=repo_root, timeout=timeout)

    def parse(
        self,
        repo_root: str,
        cycle_dir: str,
        command: CommandResult,
        targets: List[str],
    ) -> Dict[str, Any]:
        try:
            data = json.loads(command.output or "[]")
        except json.JSONDecodeError:
            data = {"raw": command.output, "parse_error": True}
        return {"results": data}

    def grade(
        self,
        repo_root: str,
        cycle_dir: str,
        command: CommandResult,
        parsed: Dict[str, Any],
        targets: List[str],
    ) -> Grade:
        records = parsed.get("results", [])
        findings = []
        if isinstance(records, list):
            for item in records:
                if not isinstance(item, dict):
                    continue
                rule = item.get("code", "")
                filename = item.get("filename")
                location = item.get("location", {}) if isinstance(item.get("location"), dict) else {}
                message = item.get("message", "ruff violation")
                severity = item.get("severity", "warning") or "warning"
                findings.append(
                    build_finding(
                        identifier=f"ruff::{rule}",
                        message=message,
                        severity=severity.lower(),
                        path=filename,
                        line=int(location.get("row")) if location.get("row") else None,
                        column=int(location.get("column")) if location.get("column") else None,
                        suggestion="ruff check --fix",
                        data={"rule": rule},
                    )
                )
        status = "ok" if not findings else "failed"
        summary = "ruff clean" if status == "ok" else f"{len(findings)} issues"
        artifacts = {"ruff.json": parsed.get("results")}
        data = {"issue_count": len(findings)}
        return Grade(status=status, summary=summary, findings=findings, data=data, artifacts=artifacts)

    def suggest_fixes(
        self,
        repo_root: str,
        cycle_dir: str,
        command: CommandResult,
        parsed: Dict[str, Any],
        grade: Grade,
        targets: List[str],
    ) -> List[str]:
        if grade.status == "ok":
            return []
        scoped = " " + " ".join(targets) if targets else ""
        return [f"ruff check --fix{scoped}"]
