from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AnalyzerResult:
    name: str
    ok: bool
    skipped: bool
    summary: str
    data: Dict[str, Any]


class Analyzer:
    name: str = "base"

    def available(self) -> bool:
        return True

    def run(self, repo_root: str, cycle_dir: str, files: Optional[List[str]] = None) -> AnalyzerResult:
        raise NotImplementedError

    @staticmethod
    def _which(cmd: str) -> bool:
        return shutil.which(cmd) is not None

    @staticmethod
    def _run(cmd: List[str], cwd: Optional[str] = None, timeout: int = 1200) -> Tuple[int, str]:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.decode("utf-8", errors="replace")

    @staticmethod
    def _write_json(path: str, payload: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

