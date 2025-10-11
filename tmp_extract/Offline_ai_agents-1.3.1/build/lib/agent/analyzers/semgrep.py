from __future__ import annotations

import json
from typing import Any, Dict, List

from .base import Analyzer, CommandResult, Grade, build_finding


class SemgrepAnalyzer(Analyzer):
    name = "semgrep"

    def available(self) -> bool:
        return self._which("semgrep")

    def execute(self, repo_root: str, cycle_dir: str, targets: List[str]) -> CommandResult:
        args = ["semgrep", "--error", "--json"]
        rules = self.settings.get("rules", [])
        if isinstance(rules, str):
            rules = [rules]
        for rule in rules:
            args.extend(["--config", rule])
        args.append(".")
        timeout = int(self.settings.get("timeout", 1800))
        return self._run(args, cwd=repo_root, timeout=timeout)

    def parse(
        self,
        repo_root: str,
        cycle_dir: str,
        command: CommandResult,
        targets: List[str],
    ) -> Dict[str, Any]:
        try:
            payload = json.loads(command.output or "{}")
        except json.JSONDecodeError:
            payload = {"raw": command.output, "parse_error": True}
        return payload

    def grade(
        self,
        repo_root: str,
        cycle_dir: str,
        command: CommandResult,
        parsed: Dict[str, Any],
        targets: List[str],
    ) -> Grade:
        results = parsed.get("results", []) if isinstance(parsed, dict) else []
        findings: List = []
        for item in results:
            if not isinstance(item, dict):
                continue
            metadata = item.get('extra', {}) if isinstance(item.get('extra'), dict) else {}
            severity = metadata.get('severity', 'MEDIUM').lower()
            path = item.get('path')
            start = item.get('start', {}) if isinstance(item.get('start'), dict) else {}
            message = metadata.get('message') or item.get('message') or 'semgrep finding'
            findings.append(
                build_finding(
                    identifier=f"semgrep::{item.get('check_id', 'rule')}",
                    message=message,
                    severity=severity,
                    path=path,
                    line=start.get('line'),
                    column=start.get('col'),
                    suggestion='semgrep --fix',
                    data={'metavars': item.get('metavars', {}), 'end': item.get('end')},
                )
            )
        status = "ok" if not findings else "failed"
        summary = "semgrep clean" if status == "ok" else f"{len(findings)} findings"
        artifacts = {"semgrep.json": parsed}
        data = {"total_findings": len(findings)}
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
        return ["semgrep --fix"]
