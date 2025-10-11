from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Analyzer, AnalyzerResult, build_finding


class RepoHygieneAnalyzer(Analyzer):
    name = "repo_hygiene"

    def analyze(
        self,
        repo_root: str,
        cycle_dir: str,
        files: Optional[List[str]] = None,
    ) -> AnalyzerResult:
        todo_count = 0
        fixme_count = 0
        large_files: List[Dict[str, Any]] = []
        exec_files: List[str] = []
        repo_path = Path(repo_root)

        for root, dirs, filenames in os.walk(repo_root):
            rel_root = os.path.relpath(root, repo_root)
            if rel_root.startswith(".git") or "/.git" in rel_root:
                continue
            if rel_root.startswith("agent/artifacts"):
                continue
            for name in filenames:
                path = Path(root) / name
                try:
                    stat = path.stat()
                except FileNotFoundError:
                    continue
                rel = path.relative_to(repo_path)
                size_mb = stat.st_size / (1024 * 1024)
                if size_mb > 10:
                    large_files.append({"path": str(rel), "size_mb": round(size_mb, 2)})
                if os.access(path, os.X_OK) and path.suffix not in {".sh", ".bash", ".zsh", ""}:
                    exec_files.append(str(rel))
                if stat.st_size <= 1024 * 1024:
                    try:
                        with path.open("r", encoding="utf-8", errors="ignore") as fh:
                            for line in fh:
                                if "TODO" in line:
                                    todo_count += 1
                                if "FIXME" in line:
                                    fixme_count += 1
                    except Exception:
                        continue

        report = {
            "todo": todo_count,
            "fixme": fixme_count,
            "large_files": large_files,
            "exec_files": exec_files,
        }
        artifacts = {"repo_hygiene.json": report}

        findings: List = []
        if large_files:
            for item in large_files[:5]:
                findings.append(
                    build_finding(
                        identifier="hygiene::large_file",
                        message=f"Large file {item['path']} ({item['size_mb']} MB)",
                        severity="warning",
                        path=item["path"],
                    )
                )
        if exec_files:
            for path in exec_files[:5]:
                findings.append(
                    build_finding(
                        identifier="hygiene::exec_bit",
                        message=f"Executable bit set on {path}",
                        severity="info",
                        path=path,
                        suggestion="chmod -x",
                    )
                )
        summary = f"TODO={todo_count} FIXME={fixme_count}"
        return AnalyzerResult(
            name=self.name,
            status="ok",
            summary=summary,
            findings=findings,
            suggestions=[],
            data=report,
            artifacts=artifacts,
        )
