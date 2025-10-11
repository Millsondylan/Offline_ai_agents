"""Lightweight UI manager coordinating panels and rendering."""

from __future__ import annotations

from typing import Dict, List

from .models import AgentStatus, Task
from .panels.base import Panel, safe_addstr
from .state_manager import StateManager
from .theme import ThemeManager


class UIManager:
    """Coordinates input handling, panel switching, and layout rendering."""

    def __init__(
        self,
        *,
        screen,
        agent_controller,
        panels: List[Panel],
        theme_manager: ThemeManager,
        state_manager: StateManager,
    ) -> None:
        self.screen = screen
        self.controller = agent_controller
        self.theme_manager = theme_manager
        self.state_manager = state_manager
        self.panels: Dict[str, Panel] = {panel.panel_id: panel for panel in panels}
        self.menu_order: List[str] = [panel.panel_id for panel in panels]
        self.status = AgentStatus()
        self.dimensions = screen.getmaxyx()
        self.active_panel_id = "home" if "home" in self.panels else self.menu_order[0]
        self.breadcrumbs = ["Home"]
        self.footer_hint = self.active_panel.footer()

        # Restore panel state if persisted.
        for panel_id, panel in self.panels.items():
            stored = self.state_manager.load_panel_state(panel_id)
            if stored:
                panel.restore_state(stored)

    # ------------------------------------------------------------------
    @property
    def active_panel(self) -> Panel:
        return self.panels[self.active_panel_id]

    # ------------------------------------------------------------------
    def render(self) -> None:
        height, width = self.screen.getmaxyx()
        self.dimensions = (height, width)
        self.screen.clear()

        if height < 18 or width < 60:
            safe_addstr(self.screen, 0, 0, "Terminal too small. Resize to at least 80x24.")
            self.screen.refresh()
            return

        # Allow panel to render its own content.
        self.active_panel.render(self.screen, self.theme_manager)

        # Header
        safe_addstr(self.screen, 0, 0, "Agent Control Panel")
        status_line = (
            f"Status: {self.status.display_state} | "
            f"Cycle {self.status.cycle} | "
            f"Task {self.status.active_task or 'None'}"
        )
        safe_addstr(self.screen, 1, 0, status_line)

        # Menu
        for index, panel_id in enumerate(self.menu_order, start=1):
            panel = self.panels[panel_id]
            safe_addstr(self.screen, 3 + index, 0, f"{index}. {panel.title}")

        # Breadcrumbs and footer
        safe_addstr(self.screen, height - 2, 0, " › ".join(self.breadcrumbs))
        self.footer_hint = self.active_panel.footer()
        safe_addstr(self.screen, height - 1, 0, self.footer_hint)

        self.screen.refresh()

    # ------------------------------------------------------------------
    def handle_key(self, key: int) -> bool:
        if self.active_panel.handle_key(key):
            return True

        if 49 <= key <= 57:  # '1' to '9'
            index = key - 49  # zero based
            if 0 <= index < len(self.menu_order):
                self.switch_panel(self.menu_order[index])
                return True
            return False

        if key in (ord("t"), ord("T")):
            self.toggle_theme()
            return True

        if key == 27:  # ESC
            if self.active_panel_id != "home" and "home" in self.panels:
                self.switch_panel("home")
                return True
            return False

        return False

    # ------------------------------------------------------------------
    def switch_panel(self, panel_id: str) -> None:
        current_state = self.active_panel.capture_state()
        self.state_manager.save_panel_state(self.active_panel_id, current_state)

        self.active_panel_id = panel_id
        new_state = self.state_manager.load_panel_state(panel_id)
        if new_state:
            self.active_panel.restore_state(new_state)

        if panel_id == "home":
            self.breadcrumbs = ["Home"]
        else:
            self.breadcrumbs = ["Home", self.active_panel.title]
        self.footer_hint = self.active_panel.footer()

    # ------------------------------------------------------------------
    def update_status(self, status: AgentStatus) -> None:
        self.status = status
        home = self.panels.get("home")
        if home and hasattr(home, "update_overview"):
            tasks_panel = self.panels.get("tasks")
            tasks = getattr(tasks_panel, "tasks", [])
            completed = len([t for t in tasks if isinstance(t, Task) and t.status == "completed"])
            logs_panel = self.panels.get("logs")
            log_entries = len(getattr(logs_panel, "logs", []))
            home.update_overview(
                status=status,
                total_tasks=len(tasks),
                completed_tasks=completed,
                log_entries=log_entries,
            )

    # ------------------------------------------------------------------
    def toggle_theme(self) -> None:
        self.theme_manager.toggle()

    # ------------------------------------------------------------------
    def handle_resize(self, *, height: int, width: int) -> None:
        self.dimensions = (height, width)
