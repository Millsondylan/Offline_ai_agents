"""Help panel listing keyboard shortcuts."""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol

from agent_cli.panels.base import Panel
from agent_cli.theme import ThemeManager


class Interaction(Protocol):
    def prompt_text(self, prompt: str, *, default: str = "", title: str = "") -> Optional[str]:
        ...


_SHORTCUTS = [
    ("1-9", "Switch between panels"),
    ("Arrow Keys", "Navigate lists and menus"),
    ("Enter", "Activate selection"),
    ("ESC", "Return to Home"),
    ("T", "Toggle theme"),
    ("/", "Search within logs"),
    ("Ctrl+S", "Save in editor"),
    ("R", "Run verification suite"),
]


class HelpPanel(Panel):
    """Provide searchable keyboard reference."""

    def __init__(self, *, interaction: Optional[Interaction] = None) -> None:
        super().__init__(panel_id="help", title="Help")
        self.interaction = interaction
        self.search_term: str = ""
        self.filtered: List[tuple[str, str]] = list(_SHORTCUTS)

    def handle_key(self, key: int) -> bool:
        if key == ord("/"):
            return self._prompt_search()
        return False

    def render(self, screen, theme: ThemeManager) -> None:  # type: ignore[override]
        header = "Keyboard Shortcuts"
        if self.search_term:
            header += f" (search: {self.search_term})"
        screen.addstr(3, 2, header[: 76])
        for index, (shortcut, description) in enumerate(self.filtered):
            line = f"{index + 1}. {shortcut:<12} {description}"
            screen.addstr(5 + index, 2, line[: 76])
        if not self.filtered:
            screen.addstr(6, 2, "No shortcuts match your search.")
        screen.addstr(20, 2, "/ search shortcuts | ESC to exit"[: 76])

    def footer(self) -> str:
        return "/ search shortcuts"

    def capture_state(self) -> Dict:
        return {"search_term": self.search_term}

    def restore_state(self, state: Dict) -> None:
        self.search_term = state.get("search_term", "")
        self._apply_filter()
        self.mark_dirty()

    def _prompt_search(self) -> bool:
        if self.interaction is None:
            return False
        term = self.interaction.prompt_text("Search shortcuts", default=self.search_term, title="Help Search")
        if term is None:
            return False
        self.search_term = term.strip()
        self._apply_filter()
        self.mark_dirty()
        return True

    def _apply_filter(self) -> None:
        if not self.search_term:
            self.filtered = list(_SHORTCUTS)
            return
        term = self.search_term.lower()
        self.filtered = [
            item
            for item in _SHORTCUTS
            if term in item[0].lower() or term in item[1].lower()
        ]


__all__ = ["HelpPanel"]
