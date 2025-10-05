from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .base import Analyzer, AnalyzerResult


class PipAuditAnalyzer(Analyzer):
    name = "pip_audit"

    def available(self) -> bool:
        return self._which("pip-audit")

    def run(self, repo_root: str, cycle_dir: str, files: Optional[List[str]] = None, fix: bool = False) -> AnalyzerResult:
        if not self.available():
            return AnalyzerResult(self.name, ok=True, skipped=True, summary="pip-audit not found", data={})

        args = ["pip-audit", "--format", "json"]
        if fix:
            args.append("--fix")
        code, out = self._run(args, cwd=repo_root, timeout=1200)
        try:
            data = json.loads(out or "{}")
        except Exception:
            data = {"raw": out}
        findings = len(data) if isinstance(data, list) else int(data.get("vulnerability_count", 0)) if isinstance(data, dict) else 0
        ok = code == 0 and findings == 0
        out_path = os.path.join(cycle_dir, "pip_audit.json")
        self._write_json(out_path, data if data else {"raw": out})
        return AnalyzerResult(self.name, ok=ok, skipped=False, summary=f"findings={findings}", data=data)

