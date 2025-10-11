from __future__ import annotations

from pathlib import Path

import pytest
from agent_cli.models import TestResult
from agent_cli.panels.verification import KEY_DOWN, KEY_ENTER, VerificationPanel


@pytest.fixture()
def sample_results() -> list[TestResult]:
    return [
        TestResult(name="test_a", status="pass", duration_ms=120.0),
        TestResult(name="test_b", status="fail", duration_ms=350.0, error_message="boom"),
        TestResult(name="test_c", status="skip", duration_ms=0.0),
    ]


def _panel(tmp_path: Path, results: list[TestResult]):
    return VerificationPanel(
        results_path=tmp_path / "test_results.json",
        initial_results=list(results),
        run_delegate=lambda: results,
    )


def test_render_shows_status_icons(fake_screen, theme_manager, tmp_path, sample_results):
    panel = _panel(tmp_path, sample_results)
    panel.render(fake_screen, theme_manager)
    lines = "\n".join(fake_screen.rendered_lines())
    assert "✓ test_a" in lines
    assert "✗ test_b" in lines
    assert "⊘ test_c" in lines


def test_run_all_updates_status_and_persists(tmp_path, sample_results):
    panel = _panel(tmp_path, sample_results)
    panel.handle_key(ord("R"))
    assert panel.summary.total == 3
    saved = (tmp_path / "test_results.json").read_text()
    assert "test_b" in saved


def test_enter_shows_details(fake_screen, theme_manager, tmp_path, sample_results):
    panel = _panel(tmp_path, sample_results)
    panel.handle_key(KEY_DOWN)
    panel.handle_key(KEY_ENTER)
    panel.render(fake_screen, theme_manager)
    lines = "\n".join(fake_screen.rendered_lines())
    assert "boom" in lines
