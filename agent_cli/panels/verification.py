"""Verification panel for test execution monitoring."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from agent_cli.models import TestResult
from agent_cli.panels.base import Panel
from agent_cli.theme import ThemeManager

KEY_UP = 259
KEY_DOWN = 258
KEY_ENTER = 10

StatusIcon = {
    "pass": "✓",
    "fail": "✗",
    "skip": "⊘",
    "running": "⟳",
}


@dataclass
class Summary:
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_ms: float = 0.0


class VerificationPanel(Panel):
    """Display verification tasks and run them on demand."""

    def __init__(
        self,
        *,
        results_path: Path,
        initial_results: Optional[Sequence[TestResult]] = None,
        run_delegate: Optional[Callable[[], Sequence[TestResult]]] = None,
    ) -> None:
        super().__init__(panel_id="verify", title="Verification")
        self.results_path = Path(results_path)
        self.results_path.parent.mkdir(parents=True, exist_ok=True)

        self.tests: List[TestResult] = list(initial_results or [])
        self.selected_index = 0
        self.details_visible = False
        self.summary = Summary()
        self.is_running = False
        self.run_delegate = run_delegate
        if self.tests:
            self.summary = self._build_summary(self.tests)

    def handle_key(self, key: int) -> bool:
        if key == KEY_UP:
            if self.selected_index == 0:
                return False
            self.selected_index -= 1
            self.mark_dirty()
            return True
        if key == KEY_DOWN:
            if self.selected_index >= len(self.tests) - 1:
                return False
            self.selected_index += 1
            self.mark_dirty()
            return True
        if key == KEY_ENTER:
            self.details_visible = not self.details_visible
            self.mark_dirty()
            return True
        if key in (ord("R"), ord("r")):
            self._run_all()
            return True
        return False

    def render(self, screen, theme: ThemeManager) -> None:  # type: ignore[override]
        screen.addstr(3, 2, "Test Suite Results:")
        for index, result in enumerate(self.tests[: 12]):
            icon = StatusIcon.get(result.status, "?")
            cursor = "→" if index == self.selected_index else " "
            duration = f"({result.duration_ms:.0f}ms)" if result.duration_ms else ""
            line = f"{cursor} {icon} {result.name:<40} {duration}"
            screen.addstr(5 + index, 2, line[: 76])

        summary_line = (
            f"Summary: {self.summary.passed} passed, {self.summary.failed} failed, "
            f"{self.summary.skipped} skipped ({self.summary.duration_ms/1000:.2f}s)"
        )
        screen.addstr(18, 2, summary_line[: 76])

        if self.details_visible and self.tests:
            selected = self.tests[self.selected_index]
            screen.addstr(20, 2, f"Details: {selected.name} [{selected.status}]"[: 76])
            if selected.error_message:
                screen.addstr(21, 2, selected.error_message[: 76])
        else:
            screen.addstr(20, 2, "R Run All | Enter toggle details"[: 76])

    def footer(self) -> str:
        return "↑/↓ select | Enter details | R run suite"

    def capture_state(self) -> Dict:
        return {
            "selected_index": self.selected_index,
            "details_visible": self.details_visible,
            "tests": [result.__dict__ for result in self.tests],
        }

    def restore_state(self, state: Dict) -> None:
        self.selected_index = int(state.get("selected_index", 0))
        self.details_visible = bool(state.get("details_visible", False))
        tests_data = state.get("tests")
        if tests_data:
            restored: List[TestResult] = []
            for entry in tests_data:
                restored.append(
                    TestResult(
                        name=entry["name"],
                        status=entry["status"],
                        duration_ms=float(entry.get("duration_ms", 0.0)),
                        error_message=entry.get("error_message"),
                        output=entry.get("output", ""),
                    )
                )
            self.tests = restored
            self.summary = self._build_summary(self.tests)
        self.mark_dirty()

    # ------------------------------------------------------------------
    def _run_all(self) -> None:
        if self.run_delegate is None:
            return
        self.is_running = True
        interim = []
        for result in self.tests:
            interim.append(TestResult(result.name, "running", result.duration_ms, result.error_message))
        self.tests = interim
        self.mark_dirty()

        completed = list(self.run_delegate())
        self.tests = completed
        self.summary = self._build_summary(self.tests)
        self.is_running = False
        self._persist()
        self.mark_dirty()

    def _build_summary(self, results: Sequence[TestResult]) -> Summary:
        summary = Summary(total=len(results))
        total_duration = 0.0
        for result in results:
            total_duration += result.duration_ms
            if result.status == "pass":
                summary.passed += 1
            elif result.status == "fail":
                summary.failed += 1
            elif result.status == "skip":
                summary.skipped += 1
        summary.duration_ms = total_duration
        return summary

    def _persist(self) -> None:
        payload = {
            "summary": {
                "total": self.summary.total,
                "passed": self.summary.passed,
                "failed": self.summary.failed,
                "skipped": self.summary.skipped,
                "duration_ms": self.summary.duration_ms,
            },
            "results": [
                {
                    "name": result.name,
                    "status": result.status,
                    "duration_ms": result.duration_ms,
                    "error_message": result.error_message,
                    "output": result.output,
                }
                for result in self.tests
            ],
            "updated_at": datetime.now().isoformat(),
        }
        self.results_path.write_text(json.dumps(payload, indent=2))


__all__ = ["VerificationPanel", "KEY_UP", "KEY_DOWN", "KEY_ENTER"]
