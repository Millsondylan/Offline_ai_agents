"""UI manager orchestrating the curses layout."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

from agent_cli.models import AgentStatus
from agent_cli.panels.base import Panel
from agent_cli.state_manager import StateManager
from agent_cli.theme import ThemeManager


@dataclass
class Layout:
    header_height: int = 2
    footer_height: int = 2
    sidebar_width: int = 22


class UIManager:
    """Coordinate panels, input handling, theming, and rendering."""

    MIN_HEIGHT = 24
    MIN_WIDTH = 80

    def __init__(
        self,
        *,
        screen,
        agent_controller,
        panels: Sequence[Panel],
        theme_manager: ThemeManager,
        state_manager: StateManager,
    ) -> None:
        if not panels:
            raise ValueError("UIManager requires at least one panel")
        self.screen = screen
        self.agent_controller = agent_controller
        self.theme_manager = theme_manager
        self.state_manager = state_manager
        self.layout = Layout()

        self._panel_order: List[Panel] = list(panels)
        self._panels_by_id: Dict[str, Panel] = {panel.panel_id: panel for panel in self._panel_order}
        if len(self._panel_order) != len(self._panels_by_id):
            raise ValueError("Panel identifiers must be unique")

        self._active_panel: Panel = self._panel_order[0]
        self._active_panel.on_focus()
        self._home_panel_id = self._active_panel.panel_id

        self._dimensions = self.screen.getmaxyx()
        self._breadcrumbs: List[str] = [self._panel_order[0].title]
        self._footer_hint: str = self._active_panel.footer() or "Press 1-9 to navigate"
        self._agent_status: AgentStatus = AgentStatus(
            lifecycle_state="idle",
            cycle=0,
            active_task="",
            progress=0.0,
            message="Idle",
            is_connected=True,
            updated_at=self._panel_order[0].capture_state().get("updated_at", None) or agent_controller.status.updated_at,
        )
        self._needs_render = True

        if hasattr(self.agent_controller, "subscribe_status"):
            self.agent_controller.subscribe_status(self.update_status)

        self._restore_panel_state(self._active_panel)

    @property
    def active_panel(self) -> Panel:
        return self._active_panel

    @property
    def breadcrumbs(self) -> List[str]:
        return list(self._breadcrumbs)

    @property
    def footer_hint(self) -> str:
        return self._footer_hint

    @property
    def dimensions(self) -> tuple[int, int]:
        return self._dimensions

    def toggle_theme(self) -> None:
        self.theme_manager.toggle_theme()
        self._needs_render = True

    def handle_resize(self, *, height: int, width: int) -> None:
        self._dimensions = (height, width)
        self._needs_render = True

    def switch_panel(self, panel_id: str) -> None:
        if panel_id not in self._panels_by_id:
            return
        if self._active_panel.panel_id == panel_id:
            return

        # persist outgoing panel state
        self.state_manager.save_panel_state(
            self._active_panel.panel_id, self._active_panel.capture_state()
        )
        self._active_panel.on_blur()

        target = self._panels_by_id[panel_id]
        target_state = self.state_manager.load_panel_state(panel_id)
        if target_state:
            target.restore_state(target_state)
        target.on_focus()
        self._active_panel = target
        self._update_breadcrumbs(target)
        self._update_footer_hint()
        self._needs_render = True

    def _update_breadcrumbs(self, panel: Panel) -> None:
        home_title = self._panels_by_id[self._home_panel_id].title
        if panel.panel_id == self._home_panel_id:
            self._breadcrumbs = [home_title]
        else:
            self._breadcrumbs = [home_title, panel.title]

    def _update_footer_hint(self) -> None:
        hint = self._active_panel.footer()
        self._footer_hint = hint or "Press 1-9 to navigate"

    def handle_key(self, key: int) -> bool:
        if key in (ord("t"), ord("T")):
            self.toggle_theme()
            return True
        if key == 27:  # ESC
            self.switch_panel(self._home_panel_id)
            return True
        if ord("1") <= key <= ord("9"):
            index = key - ord("1")
            if index < len(self._panel_order):
                self.switch_panel(self._panel_order[index].panel_id)
                return True
            return False

        handled = self._active_panel.handle_key(key)
        if handled:
            self.state_manager.save_panel_state(
                self._active_panel.panel_id, self._active_panel.capture_state()
            )
            self._needs_render = True
        return handled

    def render(self) -> None:
        if not self._needs_render:
            return

        height, width = self._dimensions
        self.screen.clear()

        if height < self.MIN_HEIGHT or width < self.MIN_WIDTH:
            warning = f"Terminal too small (min {self.MIN_WIDTH}x{self.MIN_HEIGHT})"
            self.screen.addstr(0, 0, warning[: max(0, width - 1)])
            self.screen.refresh()
            self._needs_render = False
            return

        self._render_header(width)
        self._render_menu()
        self._render_status_sidebar(width)
        self._render_content_area()
        self._render_footer(width, height)

        self.screen.refresh()
        self._needs_render = False
        self._active_panel.mark_clean()

    def _render_header(self, width: int) -> None:
        status_text = self._agent_status.status_display()
        progress = self._agent_status.progress_percent()
        cycle = self._agent_status.cycle
        header = f"Agent Control Panel | {status_text} | Cycle {cycle} | Progress {progress}%"
        self.screen.addstr(0, 1, header[: max(0, width - 2)])

    def _render_menu(self) -> None:
        self.screen.addstr(2, 1, "Main Menu")
        for index, panel in enumerate(self._panel_order, start=1):
            marker = "→" if panel.panel_id == self._active_panel.panel_id else " "
            entry = f"{marker} {index}. {panel.title}"
            self.screen.addstr(2 + index, 1, entry)

    def _render_status_sidebar(self, width: int) -> None:
        sidebar_x = max(width - self.layout.sidebar_width, 40)
        self.screen.addstr(2, sidebar_x, "Status")
        state = self._agent_status
        connection = "Connected" if state.is_connected else "Disconnected"
        self.screen.addstr(3, sidebar_x, f"State : {state.lifecycle_state.capitalize()}")
        self.screen.addstr(4, sidebar_x, f"Cycle : {state.cycle}")
        self.screen.addstr(5, sidebar_x, f"Task  : {state.active_task or 'None'}")
        self.screen.addstr(6, sidebar_x, f"Msg   : {state.message}")
        self.screen.addstr(7, sidebar_x, f"Link  : {connection}")

    def _render_content_area(self) -> None:
        self.active_panel.render(self.screen, self.theme_manager)

    def _render_footer(self, width: int, height: int) -> None:
        breadcrumb_line = " > ".join(self._breadcrumbs)
        self.screen.addstr(height - 2, 1, f"Breadcrumbs: {breadcrumb_line}"[: max(0, width - 2)])
        hint_text = f"Hint: {self._footer_hint}"
        self.screen.addstr(height - 1, 1, hint_text[: max(0, width - 2)])

    def update_status(self, status: AgentStatus) -> None:
        self._agent_status = status
        self._needs_render = True

    def _restore_panel_state(self, panel: Panel) -> None:
        state = self.state_manager.load_panel_state(panel.panel_id)
        if state:
            panel.restore_state(state)
