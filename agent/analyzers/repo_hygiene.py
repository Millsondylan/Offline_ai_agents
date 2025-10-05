from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from .base import Analyzer, AnalyzerResult


class RepoHygieneAnalyzer(Analyzer):
    name = "repo_hygiene"

    def run(self, repo_root: str, cycle_dir: str, files: Optional[List[str]] = None) -> AnalyzerResult:
        todo_count = 0
        fixme_count = 0
        large_files: List[Dict[str, Any]] = []
        exec_files: List[str] = []

        for root, _, filenames in os.walk(repo_root):
            # Skip VCS and artifacts
            if any(seg.startswith('.') for seg in os.path.relpath(root, repo_root).split(os.sep) if seg):
                # allow .github but skip .git, .venv, etc.
                if os.path.basename(root) not in (".github",):
                    continue
            for fn in filenames:
                path = os.path.join(root, fn)
                try:
                    st = os.stat(path)
                except FileNotFoundError:
                    continue
                size_mb = st.st_size / (1024 * 1024)
                if size_mb > 10:
                    large_files.append({"path": os.path.relpath(path, repo_root), "size_mb": round(size_mb, 2)})
                if os.access(path, os.X_OK) and not fn.endswith((".sh", ".bash", ".zsh")):
                    exec_files.append(os.path.relpath(path, repo_root))
                # light content scan for text files
                if st.st_size < 1024 * 1024:  # 1MB
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                if "TODO" in line:
                                    todo_count += 1
                                if "FIXME" in line:
                                    fixme_count += 1
                    except Exception:
                        pass

        report: Dict[str, Any] = {
            "todo": todo_count,
            "fixme": fixme_count,
            "large_files": large_files,
            "exec_files": exec_files,
        }
        out_path = os.path.join(cycle_dir, "repo_hygiene.json")
        self._write_json(out_path, report)
        # Never block on hygiene; treat as warning only
        return AnalyzerResult(self.name, ok=True, skipped=False, summary=f"todo={todo_count}, fixme={fixme_count}", data=report)

