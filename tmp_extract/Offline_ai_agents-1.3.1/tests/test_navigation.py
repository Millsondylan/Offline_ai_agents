from __future__ import annotations


def test_handle_key_delegates_to_active_panel(ui_manager):
    active = ui_manager.active_panel
    assert active.state["scroll"] == 0
    handled = ui_manager.handle_key(ord("j"))
    assert handled is True
    assert active.state["scroll"] == 1


def test_handle_key_switches_panels_with_numbers(ui_manager):
    handled = ui_manager.handle_key(ord("5"))
    assert handled is True
    assert ui_manager.active_panel.panel_id == "editor"


def test_invalid_numeric_key_is_ignored(ui_manager):
    handled = ui_manager.handle_key(ord("0"))
    assert handled is False
    assert ui_manager.active_panel.panel_id == "home"


def test_theme_toggles_with_uppercase_t(ui_manager, theme_manager):
    assert theme_manager.active_theme == "dark"
    handled = ui_manager.handle_key(ord("T"))
    assert handled is True
    assert theme_manager.active_theme == "light"


def test_escape_returns_to_home_panel(ui_manager):
    ui_manager.switch_panel("logs")
    assert ui_manager.active_panel.panel_id == "logs"
    handled = ui_manager.handle_key(27)  # ESC key code
    assert handled is True
    assert ui_manager.active_panel.panel_id == "home"
