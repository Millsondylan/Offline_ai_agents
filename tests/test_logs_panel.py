from __future__ import annotations

import json
from datetime import datetime

from agent_cli.models import LogEntry
from agent_cli.panels.logs import KEY_DOWN, KEY_UP, LogsPanel


def _log(level: str, message: str, cycle: int = 1) -> LogEntry:
    return LogEntry(
        cycle=cycle,
        timestamp=datetime(2024, 1, 1, 12, 0, cycle % 60),
        level=level,
        message=message,
    )


def _panel(tmp_path, interaction) -> LogsPanel:
    return LogsPanel(log_dir=tmp_path / "logs", interaction=interaction)


def test_log_panel_renders_entries(fake_screen, theme_manager, stub_interaction, tmp_path):
    panel = _panel(tmp_path, stub_interaction)
    panel.add_log(_log("INFO", "Starting"))
    panel.add_log(_log("ERROR", "Failure"))

    panel.render(fake_screen, theme_manager)
    lines = "\n".join(fake_screen.rendered_lines())
    assert "Starting" in lines
    assert "Failure" in lines


def test_filter_toggles_error_only(stub_interaction, tmp_path):
    panel = _panel(tmp_path, stub_interaction)
    panel.add_log(_log("INFO", "Info message"))
    panel.add_log(_log("ERROR", "Error message"))

    panel.handle_key(ord("F"))
    assert all(entry.level == "ERROR" for entry in panel.visible_logs)

    panel.handle_key(ord("F"))
    assert any(entry.level == "INFO" for entry in panel.visible_logs)


def test_search_highlights_matches(stub_interaction, tmp_path):
    panel = _panel(tmp_path, stub_interaction)
    panel.add_log(_log("INFO", "Retry network call"))
    panel.add_log(_log("ERROR", "Network failure"))

    stub_interaction.queue_prompt("network")
    panel.handle_key(ord("/"))

    assert panel.search_term == "network"
    assert len(panel.search_matches) >= 1

    panel.handle_key(ord("n"))
    assert panel.current_match_index == 0


def test_save_logs_creates_timestamped_file(stub_interaction, tmp_path):
    panel = _panel(tmp_path, stub_interaction)
    panel.add_log(_log("INFO", "Something happened"))

    panel.handle_key(ord("S"))
    files = list((tmp_path / "logs").glob("*.log"))
    assert files, "Expected a log file to be created"

    saved = json.loads(panel.last_saved_metadata.read_text())
    assert saved["entries"] == 1


def test_clear_requires_confirmation(stub_interaction, tmp_path):
    panel = _panel(tmp_path, stub_interaction)
    panel.add_log(_log("INFO", "Will clear"))

    stub_interaction.queue_confirm(False)
    panel.handle_key(ord("C"))
    assert panel.logs

    stub_interaction.queue_confirm(True)
    panel.handle_key(ord("C"))
    assert not panel.logs


def test_scroll_updates_offset(stub_interaction, tmp_path):
    panel = _panel(tmp_path, stub_interaction)
    for idx in range(50):
        panel.add_log(_log("INFO", f"Log {idx}", cycle=idx))

    panel.handle_key(KEY_DOWN)
    assert panel.scroll_offset > 0
    panel.handle_key(KEY_UP)
    assert panel.scroll_offset == 0
