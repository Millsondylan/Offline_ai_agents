from __future__ import annotations

import json
from typing import Any, Dict, List

from .base import Analyzer, CommandResult, Grade, build_finding


class PipAuditAnalyzer(Analyzer):
    name = "pip_audit"

    def available(self) -> bool:
        return self._which("pip-audit")

    def execute(self, repo_root: str, cycle_dir: str, targets: List[str]) -> CommandResult:
        args = ["pip-audit", "--format", "json"]
        if self.settings.get("fix"):
            args.append("--fix")
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
        items: List[Dict[str, Any]] = []
        if isinstance(parsed, list):
            items = [i for i in parsed if isinstance(i, dict)]
        elif isinstance(parsed, dict) and "dependencies" in parsed:
            # pip-audit>=2 outputs {dependencies:[{name,version,vulns:[]}]}
            for dep in parsed.get("dependencies", []):
                vulns = dep.get("vulns", []) if isinstance(dep, dict) else []
                for vuln in vulns:
                    if isinstance(vuln, dict):
                        data = dict(vuln)
                        data["dependency"] = dep.get("name")
                        items.append(data)
        findings: List = []
        for entry in items:
            vuln_id = entry.get("id") or entry.get("identifier") or "unknown"
            severity = (entry.get("severity") or "medium").lower()
            fix_versions = entry.get("fix_version") or entry.get("fix_versions")
            message = entry.get("description") or entry.get("title") or "pip-audit vulnerability"
            suggestion = None
            if fix_versions:
                if isinstance(fix_versions, list):
                    suggestion = f"upgrade to {'/'.join(fix_versions)}"
                else:
                    suggestion = f"upgrade to {fix_versions}"
            findings.append(
                build_finding(
                    identifier=f"pip-audit::{vuln_id}",
                    message=message,
                    severity=severity,
                    suggestion=suggestion,
                    data={
                        "dependency": entry.get("dependency") or entry.get("name"),
                        "current_version": entry.get("version"),
                        "advisory": entry.get("advisory"),
                    },
                )
            )
        status = "ok" if not findings else "failed"
        summary = "pip-audit clean" if status == "ok" else f"{len(findings)} vulnerable packages"
        artifacts = {"pip_audit.json": parsed}
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
        if self.settings.get("fix"):
            return []
        return ["pip-audit --fix"]
