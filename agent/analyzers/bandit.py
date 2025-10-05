from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .base import Analyzer, AnalyzerResult


class BanditAnalyzer(Analyzer):
    name = "bandit"

    def available(self) -> bool:
        return self._which("bandit")

    def run(self, repo_root: str, cycle_dir: str, files: Optional[List[str]] = None) -> AnalyzerResult:
        if not self.available():
            return AnalyzerResult(self.name, ok=True, skipped=True, summary="bandit not found", data={})

        code, out = self._run(["bandit", "-q", "-r", ".", "-f", "json"], cwd=repo_root, timeout=900)
        try:
            data = json.loads(out or "{}")
        except Exception:
            data = {"raw": out}

        issues = int(data.get("metrics", {}).get("_totals", {}).get("SEVERITY.HIGH", 0)) + int(
            data.get("metrics", {}).get("_totals", {}).get("SEVERITY.CRITICAL", 0)
        )
        ok = issues == 0
        out_path = os.path.join(cycle_dir, "bandit.json")
        self._write_json(out_path, data if data else {"raw": out})
        return AnalyzerResult(self.name, ok=ok, skipped=False, summary=f"high_critical={issues}", data=data)

