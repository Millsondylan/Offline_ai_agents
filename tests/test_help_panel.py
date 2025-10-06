from __future__ import annotations

from agent_cli.panels.help import HelpPanel


def test_help_panel_contains_shortcuts(fake_screen, theme_manager, stub_interaction):
    panel = HelpPanel(interaction=stub_interaction)
    panel.render(fake_screen, theme_manager)
    lines = "\n".join(fake_screen.rendered_lines())
    assert "1. Home" in lines
    assert "ESC" in lines


def test_search_filters_results(fake_screen, theme_manager, stub_interaction):
    panel = HelpPanel(interaction=stub_interaction)
    stub_interaction.queue_prompt("logs")
    panel.handle_key(ord("/"))
    panel.render(fake_screen, theme_manager)
    lines = "\n".join(fake_screen.rendered_lines())
    assert "Logs" in lines
    assert "Home" not in lines
