from __future__ import annotations

from pathlib import Path

from agent_cli.panels.model_config import (
    KEY_DOWN,
    KEY_ENTER,
    KEY_LEFT,
    KEY_RIGHT,
    ModelConfigPanel,
)


def _panel(tmp_path: Path):
    return ModelConfigPanel(config_path=tmp_path / "model_config.json")


def test_lists_models_and_marks_current(tmp_path):
    panel = _panel(tmp_path)
    assert panel.models[panel.selected_model_index]["name"] == panel.selected_model


def test_switch_model_updates_selection(tmp_path):
    panel = _panel(tmp_path)
    panel.handle_key(KEY_DOWN)
    panel.handle_key(KEY_ENTER)
    assert panel.selected_model != "gpt-4"


def test_adjust_temperature_with_arrows(tmp_path):
    panel = _panel(tmp_path)
    # Move selection to temperature row
    panel.cursor_index = len(panel.models)
    initial = panel.config.temperature
    panel.handle_key(KEY_RIGHT)
    assert panel.config.temperature > initial
    panel.handle_key(KEY_LEFT)
    assert round(panel.config.temperature, 2) == round(initial, 2)


def test_reset_restores_defaults(tmp_path):
    panel = _panel(tmp_path)
    panel.cursor_index = len(panel.models) + 1
    panel.handle_key(KEY_RIGHT)
    panel.handle_key(ord("R"))
    assert panel.config.max_tokens == 2048


def test_persist_writes_to_disk(tmp_path):
    panel = _panel(tmp_path)
    panel.cursor_index = len(panel.models)
    panel.handle_key(KEY_RIGHT)
    saved_path = tmp_path / "model_config.json"
    data = saved_path.read_text()
    assert "temperature" in data
