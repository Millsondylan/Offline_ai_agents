from __future__ import annotations

import json
from pathlib import Path

from agent_cli.panels.task_manager import KEY_DOWN, KEY_NPAGE, KEY_PPAGE, KEY_UP, TaskManagerPanel


def _create_panel(tmp_path: Path, interaction):
    storage = tmp_path / "tasks.json"
    return TaskManagerPanel(storage_path=storage, interaction=interaction)


def test_empty_state_renders_message(fake_screen, theme_manager, stub_interaction, tmp_path):
    panel = _create_panel(tmp_path, stub_interaction)
    panel.render(fake_screen, theme_manager)
    assert fake_screen.contains("No tasks yet. Press N to create.")


def test_create_task_via_keyboard(fake_screen, theme_manager, stub_interaction, tmp_path):
    panel = _create_panel(tmp_path, stub_interaction)
    stub_interaction.queue_prompt("Implement UI manager")
    stub_interaction.queue_prompt("high")

    handled = panel.handle_key(ord("N"))
    assert handled is True
    assert len(panel.tasks) == 1
    panel.render(fake_screen, theme_manager)
    assert fake_screen.contains("Implement UI manager")

    data = json.loads((tmp_path / "tasks.json").read_text())
    assert data[0]["description"] == "Implement UI manager"
    assert data[0]["priority"] == "high"


def test_edit_task_updates_description(stub_interaction, tmp_path):
    panel = _create_panel(tmp_path, stub_interaction)
    panel.create_task("Draft tests", priority="medium")

    stub_interaction.queue_prompt("Draft integration tests")
    handled = panel.handle_key(ord("E"))
    assert handled is True

    assert panel.tasks[0].description == "Draft integration tests"
    stored = json.loads((tmp_path / "tasks.json").read_text())
    assert stored[0]["description"] == "Draft integration tests"


def test_delete_task_requires_confirmation(stub_interaction, tmp_path):
    panel = _create_panel(tmp_path, stub_interaction)
    panel.create_task("Remove legacy code", priority="low")

    stub_interaction.queue_confirm(False)
    assert panel.handle_key(ord("D")) is False
    assert len(panel.tasks) == 1

    stub_interaction.queue_confirm(True)
    assert panel.handle_key(ord("D")) is True
    assert len(panel.tasks) == 0
    data = json.loads((tmp_path / "tasks.json").read_text())
    assert data == []


def test_activate_task_marks_indicator(fake_screen, theme_manager, stub_interaction, tmp_path):
    panel = _create_panel(tmp_path, stub_interaction)
    panel.create_task("Research APIs", priority="medium")
    panel.create_task("Write docs", priority="low")

    handled = panel.handle_key(ord("A"))
    assert handled is True
    assert panel.active_task_id == panel.tasks[0].id
    panel.render(fake_screen, theme_manager)
    lines = "\n".join(fake_screen.rendered_lines())
    assert "[ACTIVE]" in lines


def test_tasks_persist_between_sessions(stub_interaction, tmp_path):
    storage = tmp_path / "tasks.json"
    panel = TaskManagerPanel(storage_path=storage, interaction=stub_interaction)
    panel.create_task("Initial task", priority="high")

    second = TaskManagerPanel(storage_path=storage, interaction=stub_interaction)
    assert len(second.tasks) == 1
    assert second.tasks[0].description == "Initial task"


def test_pagination_handles_large_task_sets(stub_interaction, tmp_path):
    panel = _create_panel(tmp_path, stub_interaction)
    for idx in range(60):
        panel.create_task(f"Task {idx}")

    assert panel.view_offset == 0
    panel.handle_key(KEY_NPAGE)
    assert panel.view_offset > 0
    panel.handle_key(KEY_PPAGE)
    assert panel.view_offset == 0


def test_arrow_navigation_wraps_within_bounds(stub_interaction, tmp_path):
    panel = _create_panel(tmp_path, stub_interaction)
    for idx in range(3):
        panel.create_task(f"Task {idx}")

    panel.handle_key(KEY_DOWN)
    assert panel.selected_index == 1
    panel.handle_key(KEY_UP)
    assert panel.selected_index == 0
    panel.handle_key(KEY_UP)
    assert panel.selected_index == 0


def test_capture_and_restore_state(stub_interaction, tmp_path):
    panel = _create_panel(tmp_path, stub_interaction)
    for idx in range(5):
        panel.create_task(f"Task {idx}")
    panel.handle_key(KEY_DOWN)
    panel.handle_key(KEY_DOWN)
    panel.handle_key(KEY_NPAGE)

    state = panel.capture_state()
    restored = _create_panel(tmp_path, stub_interaction)
    restored.restore_state(state)

    assert restored.selected_index == state["selected_index"]
    assert restored.view_offset == state["view_offset"]
