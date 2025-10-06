"""Panel foundation for the control panel UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from agent_cli.theme import ThemeManager


@dataclass
class PanelContext:
    """Contextual information passed to panels during render."""

    height: int
    width: int
    start_y: int
    start_x: int
    breadcrumbs: List[str] = field(default_factory=list)


class Panel:
    """Base class for panels with state persistence hooks."""

    def __init__(self, panel_id: str, title: str) -> None:
        self.panel_id = panel_id
        self.title = title
        self._active = False
        self._needs_render = True

    @property
    def is_active(self) -> bool:
        return self._active

    def render(self, screen, theme: ThemeManager) -> None:  # pragma: no cover - abstract contract
        raise NotImplementedError

    def handle_key(self, key: int) -> bool:
        return False

    def on_focus(self) -> None:
        self._active = True
        self._needs_render = True

    def on_blur(self) -> None:
        self._active = False

    def capture_state(self) -> Dict[str, Any]:
        return {}

    def restore_state(self, state: Dict[str, Any]) -> None:
        if state:
            self._needs_render = True

    def footer(self) -> str:
        return ""

    def breadcrumbs(self) -> Iterable[str]:
        return [self.title]

    def mark_dirty(self) -> None:
        self._needs_render = True

    @property
    def needs_render(self) -> bool:
        return self._needs_render

    def mark_clean(self) -> None:
        self._needs_render = False


__all__ = ["Panel", "PanelContext"]
