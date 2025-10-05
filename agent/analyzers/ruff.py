from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .base import Analyzer, AnalyzerResult


class RuffAnalyzer(Analyzer):
    name = "ruff"

    def available(self) -> bool:
        return self._which("ruff")

    def run(self, repo_root: str, cycle_dir: str, files: Optional[List[str]] = None) -> AnalyzerResult:
        if not self.available():
            return AnalyzerResult(self.name, ok=True, skipped=True, summary="ruff not found", data={})

        targets = files or []
        args = ["ruff", "check", "--output-format", "json"]
        if targets:
            args.extend(targets)
        code, out = self._run(args, cwd=repo_root, timeout=600)
        data: Dict[str, Any]
        try:
            data = json.loads(out or "{}")
        except Exception:
            data = {"raw": out}

        problems = 0
        if isinstance(data, list):
            problems = sum(1 for _ in data)
        elif isinstance(data, dict) and "summary" in data:
            problems = int(data.get("summary", {}).get("error_count", 0))
        ok = code == 0 and problems == 0

        out_path = os.path.join(cycle_dir, "ruff.json")
        self._write_json(out_path, data if data else {"raw": out})
        return AnalyzerResult(self.name, ok=ok, skipped=False, summary=f"issues={problems}", data=data)

