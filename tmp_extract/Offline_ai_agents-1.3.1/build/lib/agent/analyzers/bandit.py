from __future__ import annotations

import json
from typing import Any, Dict, List

from .base import Analyzer, CommandResult, Grade, build_finding


class BanditAnalyzer(Analyzer):
    name = "bandit"

    def available(self) -> bool:
        return self._which("bandit")

    def execute(self, repo_root: str, cycle_dir: str, targets: List[str]) -> CommandResult:
        args = ["bandit", "-q", "-f", "json"]
        if targets:
            args.extend(sum((['-r', t] for t in targets), []))
        else:
            args.extend(["-r", "."])
        timeout = int(self.settings.get("timeout", 900))
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
            severity = str(item.get("issue_severity", "LOW")).lower()
            finding = build_finding(
                identifier=f"bandit::{item.get('test_id', 'UNKNOWN')}",
                message=item.get("issue_text", "bandit finding"),
                severity=severity,
                path=item.get("filename"),
                line=item.get("line_number"),
                suggestion=item.get("more_info"),
                data={"confidence": item.get("issue_confidence"), "code": item.get("code")},
            )
            findings.append(finding)
        status = "ok" if not findings else "failed"
        summary = "bandit clean" if status == "ok" else f"{len(findings)} findings"
        artifacts = {"bandit.json": parsed}
        data = {
            "high_count": sum(1 for f in findings if f.severity.lower() in {"high", "critical"}),
            "total_findings": len(findings),
        }
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
        scope = " ".join(targets) if targets else "."
        return [f"bandit -r {scope}"]
