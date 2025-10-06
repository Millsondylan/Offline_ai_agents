from __future__ import annotations

from pathlib import Path

import pytest

from agent_cli.state_manager import StateManager


def test_state_manager_persists_panel_state(tmp_path: Path):
    manager = StateManager(base_path=tmp_path)
    manager.save_panel_state("tasks", {"scroll": 3, "selection": 10})

    restored = StateManager(base_path=tmp_path)
    state = restored.load_panel_state("tasks")
    assert state == {"scroll": 3, "selection": 10}


def test_state_manager_returns_empty_when_missing(tmp_path: Path):
    manager = StateManager(base_path=tmp_path)
    state = manager.load_panel_state("missing")
    assert state == {}


def test_state_manager_handles_corrupt_state_file(tmp_path: Path):
    state_file = tmp_path / "panel_state_tasks.json"
    state_file.write_text("not-json")

    manager = StateManager(base_path=tmp_path)
    assert manager.load_panel_state("tasks") == {}


def test_state_manager_supports_undo_redo(tmp_path: Path):
    manager = StateManager(base_path=tmp_path)
    manager.record_action("tasks", {"selection": 1})
    manager.record_action("tasks", {"selection": 2})
    manager.record_action("tasks", {"selection": 3})

    assert manager.undo("tasks") == {"selection": 2}
    assert manager.undo("tasks") == {"selection": 1}
    assert manager.undo("tasks") is None

    assert manager.redo("tasks") == {"selection": 2}
    assert manager.redo("tasks") == {"selection": 3}
    assert manager.redo("tasks") is None
