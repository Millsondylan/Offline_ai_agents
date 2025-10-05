from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .base import Analyzer, AnalyzerResult


class PytestCoverageAnalyzer(Analyzer):
    name = "pytest_cov"

    def available(self) -> bool:
        return self._which("pytest") and self._which("coverage")

    def run(self, repo_root: str, cycle_dir: str, files: Optional[List[str]] = None) -> AnalyzerResult:
        if not self.available():
            return AnalyzerResult(self.name, ok=True, skipped=True, summary="pytest/coverage not found", data={})

        junit_path = os.path.join(cycle_dir, "junit.xml")
        code1, out1 = self._run(["coverage", "erase"], cwd=repo_root, timeout=120)
        code2, out2 = self._run(["coverage", "run", "-m", "pytest", "-q", "--maxfail=1", "--disable-warnings", f"--junitxml={junit_path}"], cwd=repo_root, timeout=1800)
        code3, out3 = self._run(["coverage", "json"], cwd=repo_root, timeout=120)

        cov_json_path = os.path.join(repo_root, "coverage.json")
        cov_data: Dict[str, Any] = {}
        if os.path.exists(cov_json_path):
            try:
                with open(cov_json_path, "r", encoding="utf-8") as f:
                    cov_data = json.load(f)
            except Exception:
                cov_data = {"raw": "failed to parse coverage.json"}

        # Move coverage.json into artifacts directory for consistency
        if os.path.exists(cov_json_path):
            try:
                os.replace(cov_json_path, os.path.join(cycle_dir, "coverage.json"))
            except Exception:
                pass

        ok = code2 == 0
        summary = f"pytest_ok={ok}"
        # write a minimal report
        report = {
            "pytest_code": code2,
            "coverage_json": cov_data,
            "stdout": out1 + "\n" + out2 + "\n" + out3,
        }
        out_path = os.path.join(cycle_dir, "pytest_cov.json")
        self._write_json(out_path, report)
        return AnalyzerResult(self.name, ok=ok, skipped=False, summary=summary, data=report)

