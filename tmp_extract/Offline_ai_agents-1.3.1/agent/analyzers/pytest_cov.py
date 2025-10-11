from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Analyzer, AnalyzerResult, build_finding


class PytestCoverageAnalyzer(Analyzer):
    name = "pytest_cov"

    def available(self) -> bool:
        return self._which("pytest") and self._which("coverage")

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
                summary="pytest/coverage not available",
                findings=[],
                suggestions=[],
                data={},
                artifacts={},
            )

        timeout = int(self.settings.get("timeout", 3600))
        junit_path = Path(cycle_dir) / "junit.xml"

        erase_res = self._run(["coverage", "erase"], cwd=repo_root, timeout=timeout)

        cmd = [
            "coverage",
            "run",
            "-m",
            "pytest",
            "-q",
            "--maxfail=1",
            "--disable-warnings",
            f"--junitxml={junit_path}",
        ]
        extra_args = self.settings.get("args") or []
        if isinstance(extra_args, str):
            extra_args = [extra_args]
        cmd.extend(extra_args)
        if files:
            cmd.extend(files)

        pytest_res = self._run(cmd, cwd=repo_root, timeout=timeout)

        cov_res = self._run(["coverage", "json"], cwd=repo_root, timeout=timeout)

        cov_json_path = Path(repo_root) / "coverage.json"
        cov_payload: Dict[str, Any] = {}
        if cov_json_path.exists():
            try:
                cov_payload = json.loads(cov_json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                cov_payload = {"raw": cov_json_path.read_text(encoding="utf-8", errors="replace")}
            # move into artifacts dir to avoid polluting working tree
            dest = Path(cycle_dir) / "coverage.json"
            try:
                cov_json_path.replace(dest)
            except Exception:
                # fallback copy
                dest.write_text(json.dumps(cov_payload, indent=2))

        report = {
            "pytest_code": pytest_res.code,
            "pytest_output": pytest_res.output,
            "coverage": cov_payload,
            "coverage_exit": cov_res.code,
            "erase_exit": erase_res.code,
        }

        artifacts = {"pytest_cov.json": report}
        findings = []
        suggestions: List[str] = []
        if pytest_res.code != 0:
            findings.append(
                build_finding(
                    identifier="pytest::failures",
                    message="Pytest reported failures",
                    severity="critical",
                    suggestion="pytest -q",
                    data={"output": pytest_res.output[:2000]},
                )
            )
            suggestions.append("pytest -q")
        if cov_res.code != 0:
            findings.append(
                build_finding(
                    identifier="coverage::json",
                    message="coverage json generation failed",
                    severity="warning",
                    suggestion="coverage json",
                    data={"output": cov_res.output[:2000]},
                )
            )
            suggestions.append("coverage json")

        status = "ok" if pytest_res.code == 0 and cov_res.code == 0 else "failed"
        summary = "tests passed" if status == "ok" else "tests failed"

        return AnalyzerResult(
            name=self.name,
            status=status,
            summary=summary,
            findings=findings,
            suggestions=suggestions,
            data=report,
            artifacts=artifacts,
            command=pytest_res,
        )
