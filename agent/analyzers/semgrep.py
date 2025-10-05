from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .base import Analyzer, AnalyzerResult


class SemgrepAnalyzer(Analyzer):
    name = "semgrep"

    def available(self) -> bool:
        return self._which("semgrep")

    def run(self, repo_root: str, cycle_dir: str, files: Optional[List[str]] = None, rules: Optional[List[str]] = None) -> AnalyzerResult:
        if not self.available():
            return AnalyzerResult(self.name, ok=True, skipped=True, summary="semgrep not found", data={})

        args = ["semgrep", "--error", "--json"]
        if rules:
            for r in rules:
                args.extend(["--config", r])
        args.append(".")
        code, out = self._run(args, cwd=repo_root, timeout=1800)
        try:
            data = json.loads(out or "{}")
        except Exception:
            data = {"raw": out}

        findings = len(data.get("results", [])) if isinstance(data, dict) else 0
        ok = code == 0 and findings == 0
        out_path = os.path.join(cycle_dir, "semgrep.json")
        self._write_json(out_path, data if data else {"raw": out})
        return AnalyzerResult(self.name, ok=ok, skipped=False, summary=f"findings={findings}", data=data)

