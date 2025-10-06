"""Execution logs panel implementation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Deque, List, Optional, Protocol

from collections import deque

from agent_cli.models import LogEntry
from agent_cli.panels.base import Panel
from agent_cli.theme import ThemeManager

KEY_UP = 259
KEY_DOWN = 258


class Interaction(Protocol):
    def prompt_text(self, prompt: str, *, default: str = "", title: str = "") -> Optional[str]:
        ...

    def confirm(self, message: str) -> bool:
        ...

    def notify(self, message: str) -> None:
        ...


class LogsPanel(Panel):
    """Display streaming logs with filtering, search, and persistence."""

    def __init__(
        self,
        *,
        log_dir: Optional[Path] = None,
        interaction: Optional[Interaction] = None,
        max_entries: int = 5000,
        page_size: int = 12,
    ) -> None:
        super().__init__(panel_id="logs", title="Execution Logs")
        self.log_dir = Path(log_dir) if log_dir else self._default_log_dir()
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.interaction = interaction
        self.logs: Deque[LogEntry] = deque(maxlen=max_entries)
        self.filter_level: Optional[str] = None
        self.page_size = max(5, page_size)
        self.scroll_offset = 0

        self.search_term: str = ""
        self.search_matches: List[int] = []
        self.current_match_index: int = -1
        self.last_saved_metadata: Optional[Path] = None

    # ------------------------------------------------------------------
    def add_log(self, entry: LogEntry) -> None:
        self.logs.append(entry)
        if self.scroll_offset == 0:
            self.scroll_offset = 0
        else:
            max_offset = max(0, len(self._filtered_logs()) - 1)
            self.scroll_offset = min(self.scroll_offset, max_offset)
        if self.search_term:
            self._recalculate_search_matches()
        self.mark_dirty()

    @property
    def visible_logs(self) -> List[LogEntry]:
        filtered = self._filtered_logs()
        if not filtered:
            return []
        end_index = len(filtered) - self.scroll_offset
        end_index = max(0, min(len(filtered), end_index))
        start_index = max(0, end_index - self.page_size)
        return filtered[start_index:end_index]

    def handle_key(self, key: int) -> bool:
        if key == KEY_UP:
            return self._scroll(1)
        if key == KEY_DOWN:
            return self._scroll(-1)
        if key in (ord("F"), ord("f")):
            return self._toggle_filter()
        if key in (ord("/"), ):
            return self._prompt_search()
        if key in (ord("n"), ):
            return self._next_match()
        if key in (ord("N"), ):
            return self._previous_match()
        if key in (ord("S"), ord("s")):
            return self._save_logs()
        if key in (ord("C"), ord("c")):
            return self._clear_logs()
        return False

    def render(self, screen, theme: ThemeManager) -> None:  # type: ignore[override]
        header = "Execution Logs"
        filter_text = f"[Filter: {self.filter_level}]" if self.filter_level else ""
        search_text = f"[Search: {self.search_term}]" if self.search_term else ""
        screen.addstr(3, 2, f"{header} {filter_text} {search_text}".strip()[: 76])
        screen.addstr(4, 2, "──────────────────────────────────────────────────────────────────")

        if not self.visible_logs:
            screen.addstr(6, 2, "No logs available yet.")
        else:
            for idx, log in enumerate(self.visible_logs):
                formatted = self._format_log(log)
                screen.addstr(5 + idx, 2, formatted[: 76])

        footer = "/ Search | F Filter | S Save | C Clear | ↑/↓ Scroll"
        screen.addstr(20, 2, footer[: 76])

    def footer(self) -> str:
        return "/ search | F filter errors | S save | C clear | n/N navigate"

    def capture_state(self) -> dict:
        return {
            "filter_level": self.filter_level,
            "scroll_offset": self.scroll_offset,
            "search_term": self.search_term,
            "current_match_index": self.current_match_index,
        }

    def restore_state(self, state: dict) -> None:
        self.filter_level = state.get("filter_level")
        self.scroll_offset = int(state.get("scroll_offset", 0))
        self.search_term = state.get("search_term", "")
        self.current_match_index = int(state.get("current_match_index", -1))
        if self.search_term:
            self._recalculate_search_matches()
        self.scroll_offset = max(0, min(self.scroll_offset, max(0, len(self._filtered_logs()) - 1)))
        self.mark_dirty()

    # ------------------------------------------------------------------
    def _scroll(self, delta: int) -> bool:
        filtered_count = len(self._filtered_logs())
        if filtered_count <= 1:
            return False
        max_offset = max(0, filtered_count - 1)
        new_offset = self.scroll_offset + delta
        new_offset = max(0, min(max_offset, new_offset))
        if new_offset == self.scroll_offset:
            return False
        self.scroll_offset = new_offset
        self.mark_dirty()
        return True

    def _toggle_filter(self) -> bool:
        self.filter_level = None if self.filter_level else "ERROR"
        self.scroll_offset = 0
        if self.search_term:
            self._recalculate_search_matches()
        self.mark_dirty()
        return True

    def _prompt_search(self) -> bool:
        if self.interaction is None:
            return False
        term = self.interaction.prompt_text("Search logs", default=self.search_term, title="Search")
        if term is None:
            return False
        self.search_term = term.strip()
        self._recalculate_search_matches()
        if self.search_matches:
            self.current_match_index = -1
        else:
            self.current_match_index = -1
        self.mark_dirty()
        return True

    def _next_match(self) -> bool:
        if not self.search_matches:
            return False
        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
        self._scroll_to_match()
        self.mark_dirty()
        return True

    def _previous_match(self) -> bool:
        if not self.search_matches:
            return False
        self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
        self._scroll_to_match()
        self.mark_dirty()
        return True

    def _save_logs(self) -> bool:
        if not self.logs:
            return False
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.log_dir / f"logs_{timestamp}.log"
        with filename.open("w", encoding="utf-8") as handle:
            for entry in self.logs:
                handle.write(self._format_log(entry) + "\n")
        metadata = {
            "path": str(filename),
            "entries": len(self.logs),
            "saved_at": datetime.now().isoformat(),
            "filter": self.filter_level,
            "search_term": self.search_term,
        }
        meta_path = self.log_dir / "last_save.json"
        meta_path.write_text(json.dumps(metadata, indent=2))
        self.last_saved_metadata = meta_path
        if self.interaction:
            self.interaction.notify(f"Saved logs to {filename.name}")
        return True

    def _clear_logs(self) -> bool:
        if self.interaction is None:
            return False
        if not self.interaction.confirm("Clear all logs?"):
            return False
        self.logs.clear()
        self.scroll_offset = 0
        self.search_matches.clear()
        self.current_match_index = -1
        self.mark_dirty()
        self.interaction.notify("Logs cleared")
        return True

    def _scroll_to_match(self) -> None:
        if not self.search_matches:
            return
        match_index = self.search_matches[self.current_match_index]
        filtered = self._filtered_logs()
        position_from_bottom = len(filtered) - match_index - 1
        self.scroll_offset = max(0, position_from_bottom)

    def _recalculate_search_matches(self) -> None:
        term = self.search_term.lower()
        if not term:
            self.search_matches = []
            self.current_match_index = -1
            return
        filtered = self._filtered_logs()
        self.search_matches = [idx for idx, entry in enumerate(filtered) if term in entry.message.lower()]
        if not self.search_matches:
            self.current_match_index = -1

    def _filtered_logs(self) -> List[LogEntry]:
        if self.filter_level is None:
            return list(self.logs)
        return [entry for entry in self.logs if entry.level == self.filter_level]

    def _format_log(self, entry: LogEntry) -> str:
        timestamp = entry.timestamp.strftime("%H:%M:%S")
        level = f"{entry.level:<5}"
        return f"[{timestamp}][Cycle {entry.cycle:04}][{level}] {entry.message}"

    def _default_log_dir(self) -> Path:
        return Path.home() / ".agent_cli" / "logs"


__all__ = ["LogsPanel", "KEY_UP", "KEY_DOWN"]
