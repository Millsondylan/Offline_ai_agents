from __future__ import annotations

from datetime import datetime, timedelta

from agent_cli.models import Thought
from agent_cli.panels.thinking import KEY_END, KEY_UP, ThinkingPanel


def _thought(cycle: int, content: str = "Thinking") -> Thought:
    return Thought(
        cycle=cycle,
        timestamp=datetime.now() + timedelta(seconds=cycle),
        content=content,
        thought_type="reasoning",
    )


def test_thinking_panel_auto_scroll(fake_screen, theme_manager):
    panel = ThinkingPanel()
    panel.add_thought(_thought(1, "Analyze requirements"))
    panel.add_thought(_thought(2, "Outline solution"))

    panel.render(fake_screen, theme_manager)
    lines = "\n".join(fake_screen.rendered_lines())
    assert "Outline solution" in lines
    assert "[LIVE]" in lines


def test_manual_scroll_disables_auto_scroll():
    panel = ThinkingPanel()
    for idx in range(5):
        panel.add_thought(_thought(idx, f"Thought {idx}"))
    assert panel.auto_scroll is True

    panel.handle_key(KEY_UP)
    assert panel.auto_scroll is False
    assert panel.scroll_offset > 0


def test_end_key_restores_live_mode():
    panel = ThinkingPanel()
    for idx in range(3):
        panel.add_thought(_thought(idx, f"Thought {idx}"))
    panel.handle_key(KEY_UP)
    panel.handle_key(KEY_END)

    assert panel.auto_scroll is True
    assert panel.scroll_offset == 0


def test_capacity_capped_at_one_thousand():
    panel = ThinkingPanel(max_thoughts=1000)
    for idx in range(1100):
        panel.add_thought(_thought(idx))
    assert len(panel.thoughts) == 1000


def test_multiline_thoughts_are_indented(fake_screen, theme_manager):
    panel = ThinkingPanel()
    panel.add_thought(_thought(1, "Line one\nLine two"))
    panel.render(fake_screen, theme_manager)
    lines = fake_screen.rendered_lines()
    assert any(line.strip().startswith("Line two") for line in lines)


def test_paused_indicator_shown_when_agent_paused(fake_screen, theme_manager):
    panel = ThinkingPanel()
    panel.set_live(False)
    panel.render(fake_screen, theme_manager)
    lines = "\n".join(fake_screen.rendered_lines())
    assert "[PAUSED]" in lines


def test_new_thought_resets_scroll_when_live():
    panel = ThinkingPanel()
    for idx in range(3):
        panel.add_thought(_thought(idx))
    panel.handle_key(KEY_UP)
    assert panel.auto_scroll is False

    panel.set_live(True)
    panel.add_thought(_thought(10, "Latest"))
    assert panel.scroll_offset == 0
    assert panel.auto_scroll is True
