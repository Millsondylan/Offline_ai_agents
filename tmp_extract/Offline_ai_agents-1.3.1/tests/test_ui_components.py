from __future__ import annotations

from datetime import datetime
from typing import Dict

import pytest
from agent_cli.models import AgentStatus
from agent_cli.panels.base import Panel
from agent_cli.state_manager import StateManager
from agent_cli.ui_manager import UIManager


class DummyPanel(Panel):
    """Minimal panel implementation for exercising the UI manager."""

    def __init__(self, panel_id: str, title: str, footer_hint: str) -> None:
        super().__init__(panel_id=panel_id, title=title)
        self.footer_hint = footer_hint
        self.render_count = 0
        self.state: Dict[str, int] = {"scroll": 0}

    def render(self, screen, theme) -> None:  # type: ignore[override]
        self.render_count += 1
        screen.addstr(5 + self.render_count, 2, f"[{self.title}] rendered {self.render_count}")

    def handle_key(self, key: int) -> bool:
        if key == ord("j"):
            self.state["scroll"] += 1
            return True
        if key == ord("k") and self.state["scroll"] > 0:
            self.state["scroll"] -= 1
            return True
        return False

    def capture_state(self) -> Dict[str, int]:
        return dict(self.state)

    def restore_state(self, state: Dict[str, int]) -> None:
        self.state.update(state)

    def footer(self) -> str:
        return self.footer_hint


@pytest.fixture()
def panel_registry() -> Dict[str, DummyPanel]:
    panels = {
        "home": DummyPanel("home", "Home", "Press 1-9 to navigate"),
        "tasks": DummyPanel("tasks", "Task Manager", "N: New task | E: Edit | A: Activate"),
        "thinking": DummyPanel("thinking", "AI Thinking", "↑/↓ Scroll | End resume live"),
        "logs": DummyPanel("logs", "Logs", "/ Search | F Filter | S Save"),
        "editor": DummyPanel("editor", "Code Editor", "E Toggle edit | Ctrl+S Save"),
        "config": DummyPanel("config", "Model Config", "←/→ Adjust | Enter Apply"),
        "verify": DummyPanel("verify", "Verification", "R Run suite | Enter details"),
        "help": DummyPanel("help", "Help", "Esc to exit help"),
        "status": DummyPanel("status", "Status", "No actions"),
    }
    return panels


@pytest.fixture()
def ui_manager(fake_screen, theme_manager, stub_agent_controller, panel_registry):
    state_manager = StateManager(base_path=None)
    manager = UIManager(
        screen=fake_screen,
        agent_controller=stub_agent_controller,
        panels=list(panel_registry.values()),
        theme_manager=theme_manager,
        state_manager=state_manager,
    )
    return manager


def test_ui_manager_renders_core_layout(ui_manager, fake_screen):
    ui_manager.render()
    lines = "\n".join(fake_screen.rendered_lines())
    assert "Agent Control Panel" in lines
    assert "Status" in lines
    for index, title in enumerate(
        [
            "Home",
            "Task Manager",
            "AI Thinking",
            "Logs",
            "Code Editor",
            "Model Config",
            "Verification",
            "Help",
            "Status",
        ],
        start=1,
    ):
        assert f"{index}. {title}" in lines


def test_ui_manager_handles_resize(ui_manager):
    assert ui_manager.dimensions == (24, 80)
    ui_manager.handle_resize(height=60, width=200)
    assert ui_manager.dimensions == (60, 200)


def test_numeric_key_switches_active_panel(ui_manager):
    assert ui_manager.active_panel.panel_id == "home"
    ui_manager.handle_key(ord("3"))
    assert ui_manager.active_panel.panel_id == "thinking"


def test_breadcrumbs_update_on_panel_switch(ui_manager):
    assert ui_manager.breadcrumbs == ["Home"]
    ui_manager.switch_panel("logs")
    assert ui_manager.breadcrumbs == ["Home", "Logs"]


def test_status_update_reflected_in_render(ui_manager, fake_screen, stub_agent_controller):
    status = AgentStatus(
        lifecycle_state="running",
        cycle=42,
        active_task="Implement UI",
        progress=0.5,
        message="Working",
        is_connected=True,
        updated_at=datetime.now(),
    )
    ui_manager.update_status(status)
    ui_manager.render()
    rendered = "\n".join(fake_screen.rendered_lines())
    assert "Running" in rendered
    assert "Cycle 42" in rendered
    assert "Implement UI" in rendered


def test_theme_toggle_updates_palette(ui_manager, theme_manager):
    assert theme_manager.active_theme == "dark"
    ui_manager.toggle_theme()
    assert theme_manager.active_theme == "light"
    ui_manager.toggle_theme()
    assert theme_manager.active_theme == "dark"


def test_footer_hint_reflects_active_panel(ui_manager):
    assert ui_manager.footer_hint.endswith("navigate")
    ui_manager.switch_panel("logs")
    assert "Search" in ui_manager.footer_hint


def test_panel_state_restored_after_switch(ui_manager):
    home_panel = ui_manager.active_panel
    home_panel.state["scroll"] = 5
    ui_manager.switch_panel("logs")
    ui_manager.switch_panel("home")
    assert home_panel.state["scroll"] == 5
