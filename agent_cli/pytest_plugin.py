"""Pytest fixtures surfaced by the compatibility layer."""

from __future__ import annotations

import asyncio
import inspect
import json
from typing import List

import pytest

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from .models import TestResult
from .panels.base import Panel
from .panels.code_editor import CodeEditorPanel
from .panels.help import HelpPanel
from .panels.home import HomePanel
from .panels.logs import LogsPanel
from .panels.model_config import ModelConfigPanel
from .panels.task_manager import TaskManagerPanel
from .panels.thinking import ThinkingPanel
from .panels.verification import VerificationPanel
from .state_manager import StateManager
from .ui_manager import UIManager


class StatusPanel(Panel):
    """Minimal status panel used by navigation tests."""

    footer_hint = "No actions"

    def __init__(self) -> None:
        super().__init__(panel_id="status", title="Status")

    def render(self, screen, theme) -> None:
        from .panels.base import safe_addstr

        safe_addstr(screen, 0, 0, "Status OK")


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    """Allow awaiting async test functions without external plugins."""

    if inspect.iscoroutinefunction(pyfuncitem.obj):
        try:
            previous_loop = asyncio.get_event_loop()
        except RuntimeError:
            previous_loop = None
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            kwargs = {name: pyfuncitem.funcargs[name] for name in pyfuncitem._fixtureinfo.argnames}
            loop.run_until_complete(pyfuncitem.obj(**kwargs))
        finally:
            loop.close()
            if previous_loop is not None:
                asyncio.set_event_loop(previous_loop)
            else:
                asyncio.set_event_loop(asyncio.new_event_loop())
        return True
    return None


@pytest.fixture()
def ui_manager(fake_screen, theme_manager, stub_agent_controller, stub_interaction, tmp_path):
    """Provide a fully wired UI manager backed by real panels."""

    # Prepare working directories for panels that persist data.
    task_storage = tmp_path / "tasks.json"
    log_dir = tmp_path / "logs"
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "main.py").write_text("print('hello')\n")
    config_path = tmp_path / "model_config.json"
    results_path = tmp_path / "test_results.json"

    def run_delegate() -> List[TestResult]:
        raw = json.loads(results_path.read_text()) if results_path.exists() else []
        return [
            TestResult(
                name=item["name"],
                status=item["status"],
                duration_ms=item["duration_ms"],
                error_message=item.get("error_message"),
            )
            for item in raw
        ]

    panels: List[Panel] = [
        HomePanel(),
        TaskManagerPanel(storage_path=task_storage, interaction=stub_interaction),
        ThinkingPanel(),
        LogsPanel(log_dir=log_dir, interaction=stub_interaction),
        CodeEditorPanel(root_path=repo_root, interaction=stub_interaction),
        ModelConfigPanel(config_path=config_path),
        VerificationPanel(results_path=results_path, initial_results=[], run_delegate=run_delegate),
        HelpPanel(interaction=stub_interaction),
        StatusPanel(),
    ]

    manager = UIManager(
        screen=fake_screen,
        agent_controller=stub_agent_controller,
        panels=panels,
        theme_manager=theme_manager,
        state_manager=StateManager(base_path=None),
    )
    return manager
