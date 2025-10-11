"""Execution log viewer panel."""

from __future__ import annotations

import curses
import json
from datetime import datetime
from pathlib import Path
from typing import List

from ..models import LogEntry
from .base import Panel, safe_addstr

KEY_UP = getattr(curses, "KEY_UP", -1)
KEY_DOWN = getattr(curses, "KEY_DOWN", -2)


class LogsPanel(Panel):
    """Displays log output with filtering, search and persistence."""

    footer_hint = "/ Search | F errors | S save | C clear"

    def __init__(self, *, log_dir: Path, interaction) -> None:
        super().__init__(panel_id="logs", title="Logs")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.interaction = interaction
        self.logs: List[LogEntry] = []
        self.filter_errors_only = False
        self.scroll_offset = 0
        self.search_term = ""
        self.search_matches: List[int] = []
        self.current_match_index = -1
        self.last_saved_metadata: Path | None = None

    # ------------------------------------------------------------------
    def add_log(self, entry: LogEntry) -> None:
        self.logs.append(entry)

    @property
    def visible_logs(self) -> List[LogEntry]:
        if not self.filter_errors_only:
            return list(self.logs)
        return [log for log in self.logs if log.level.upper() == "ERROR"]

    # ------------------------------------------------------------------
    def _recalculate_matches(self) -> None:
        self.search_matches = []
        self.current_match_index = -1
        if not self.search_term:
            return
        term = self.search_term.lower()
        for idx, entry in enumerate(self.visible_logs):
            if term in entry.message.lower():
                self.search_matches.append(idx)

    def _save_logs(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        file_path = self.log_dir / f"agent-log-{timestamp}.log"
        data = "\n".join(
            f"[{entry.timestamp.isoformat()}] {entry.level}: {entry.message}"
            for entry in self.logs
        )
        file_path.write_text(data)
        metadata = {
            "filename": file_path.name,
            "entries": len(self.logs),
            "generated_at": datetime.now().isoformat(),
        }
        metadata_path = self.log_dir / f"{file_path.stem}.json"
        metadata_path.write_text(json.dumps(metadata, indent=2))
        self.last_saved_metadata = metadata_path

    def handle_key(self, key: int) -> bool:
        if key == KEY_UP:
            if self.scroll_offset > 0:
                self.scroll_offset -= 1
            return True
        if key == KEY_DOWN:
            if self.scroll_offset < max(0, len(self.visible_logs) - 1):
                self.scroll_offset += 1
            return True
        if key in (ord("f"), ord("F")):
            self.filter_errors_only = not self.filter_errors_only
            self.scroll_offset = 0
            self._recalculate_matches()
            return True
        if key == ord("/"):
            term = self.interaction.prompt_text("Search logs")
            if term is None:
                return False
            self.search_term = term.strip()
            self._recalculate_matches()
            return True
        if key in (ord("n"), ord("N")):
            if not self.search_matches:
                return False
            if self.current_match_index == -1:
                self.current_match_index = 0
            else:
                self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
            target = self.search_matches[self.current_match_index]
            self.scroll_offset = max(0, target - 5)
            return True
        if key in (ord("s"), ord("S")):
            self._save_logs()
            self.interaction.notify("Logs saved")
            return True
        if key in (ord("c"), ord("C")):
            if not self.interaction.confirm("Clear logs?"):
                return False
            self.logs.clear()
            self.scroll_offset = 0
            self._recalculate_matches()
            return True
        return False

    # ------------------------------------------------------------------
    def render(self, screen, theme) -> None:
        safe_addstr(screen, 0, 0, "Execution Logs", theme.get("highlight"))
        if not self.logs:
            safe_addstr(screen, 2, 0, "No logs captured yet.")
            return

        entries = self.visible_logs
        start = self.scroll_offset
        for idx, entry in enumerate(entries[start : start + 20]):
            line = f"{entry.timestamp:%H:%M:%S} [{entry.level}] {entry.message}"
            safe_addstr(screen, 2 + idx, 0, line)

        if self.search_term:
            safe_addstr(
                screen,
                22,
                0,
                f"Search: {self.search_term} ({len(self.search_matches)} matches)",
                theme.get("highlight"),
            )
