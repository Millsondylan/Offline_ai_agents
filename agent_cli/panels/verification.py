"""Verification panel for running and reviewing checks."""

from __future__ import annotations

import curses
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

from ..models import TestResult
from .base import Panel, safe_addstr

KEY_UP = getattr(curses, "KEY_UP", -1)
KEY_DOWN = getattr(curses, "KEY_DOWN", -2)
KEY_ENTER = getattr(curses, "KEY_ENTER", 10)


@dataclass
class VerificationSummary:
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0


class VerificationPanel(Panel):
    """Runs verification commands and surfaces the latest results."""

    footer_hint = "R run all | Enter details | ↑/↓ navigate"

    def __init__(
        self,
        *,
        results_path: Path,
        initial_results: List[TestResult],
        run_delegate: Callable[[], List[TestResult]],
    ) -> None:
        super().__init__(panel_id="verification", title="Verification")
        self.results_path = Path(results_path)
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_delegate = run_delegate
        self.results: List[TestResult] = list(initial_results)
        self.selected_index = 0
        self.showing_detail = False
        self.summary = VerificationSummary()
        self._recalculate_summary()
        self._load_existing()

    def _load_existing(self) -> None:
        if not self.results and self.results_path.exists():
            try:
                raw = json.loads(self.results_path.read_text())
            except (OSError, json.JSONDecodeError):
                return
            self.results = [
                TestResult(
                    name=item["name"],
                    status=item["status"],
                    duration_ms=item["duration_ms"],
                    error_message=item.get("error_message"),
                )
                for item in raw
            ]
            self._recalculate_summary()

    def _persist(self) -> None:
        data = [
            {
                "name": result.name,
                "status": result.status,
                "duration_ms": result.duration_ms,
                "error_message": result.error_message,
            }
            for result in self.results
        ]
        self.results_path.write_text(json.dumps(data, indent=2))

    def _recalculate_summary(self) -> None:
        summary = VerificationSummary()
        for result in self.results:
            summary.total += 1
            status = result.status.lower()
            if status == "pass":
                summary.passed += 1
            elif status == "fail":
                summary.failed += 1
            elif status in ("skip", "skipped"):
                summary.skipped += 1
        self.summary = summary

    # ------------------------------------------------------------------
    def handle_key(self, key: int) -> bool:
        if key == KEY_UP:
            self.selected_index = max(0, self.selected_index - 1)
            self.showing_detail = False
            return True
        if key == KEY_DOWN:
            self.selected_index = min(max(0, len(self.results) - 1), self.selected_index + 1)
            self.showing_detail = False
            return True
        if key in (ord("r"), ord("R")):
            self.results = list(self.run_delegate())
            self.selected_index = min(self.selected_index, max(0, len(self.results) - 1))
            self._recalculate_summary()
            self._persist()
            return True
        if key in (KEY_ENTER, 10, 13):
            if self.results:
                self.showing_detail = True
            return True
        return False

    # ------------------------------------------------------------------
    def render(self, screen, theme) -> None:
        safe_addstr(
            screen,
            0,
            0,
            f"Verification Results — total {self.summary.total}, "
            f"passed {self.summary.passed}, failed {self.summary.failed}, skipped {self.summary.skipped}",
            theme.get("highlight"),
        )
        if not self.results:
            safe_addstr(screen, 2, 0, "No verification results recorded.")
            return

        icons = {"pass": "✓", "fail": "✗", "skip": "⊘"}

        for idx, result in enumerate(self.results):
            icon = icons.get(result.status.lower(), "•")
            prefix = ">" if idx == self.selected_index else " "
            safe_addstr(
                screen,
                2 + idx,
                0,
                f"{prefix} {icon} {result.name} ({result.duration_ms:.0f} ms)",
            )

        if self.showing_detail and self.results:
            selected = self.results[self.selected_index]
            safe_addstr(screen, 2 + len(self.results) + 1, 0, "Details:", theme.get("highlight"))
            message = selected.error_message or "No additional information."
            for offset, line in enumerate(message.splitlines() or ["No additional information."]):
                safe_addstr(screen, 2 + len(self.results) + 2 + offset, 0, line)

