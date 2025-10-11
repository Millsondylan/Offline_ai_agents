"""Simple read/write code viewer used in tests."""

from __future__ import annotations

import curses
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .base import Panel, safe_addstr

KEY_UP = getattr(curses, "KEY_UP", -1)
KEY_DOWN = getattr(curses, "KEY_DOWN", -2)
KEY_ENTER = getattr(curses, "KEY_ENTER", 10)
KEY_ESC = 27
CTRL_S = 19


@dataclass
class FileInfo:
    path: Path
    size: int
    is_readonly: bool
    modified_timestamp: float


class CodeEditorPanel(Panel):
    """Minimalist file browser + editor sufficient for unit tests."""

    footer_hint = "E edit | Ctrl+S save | ↑/↓ scroll | ESC close"

    def __init__(self, *, root_path: Path, interaction) -> None:
        super().__init__(panel_id="editor", title="Code Editor")
        self.root_path = Path(root_path)
        self.interaction = interaction
        self.files: List[FileInfo] = []
        self.current_file: Path | None = None
        self.content_lines: List[str] = []
        self.scroll_offset = 0
        self.cursor_line = 0
        self.cursor_col = 0
        self.is_editing = False
        self.is_modified = False
        self._refresh_files()

    # ------------------------------------------------------------------
    def _refresh_files(self) -> None:
        entries: List[FileInfo] = []
        for path in sorted(self.root_path.rglob("*")):
            if path.is_file():
                try:
                    stat = path.stat()
                except OSError:
                    continue
                entries.append(
                    FileInfo(
                        path=path,
                        size=stat.st_size,
                        is_readonly=not os_access_writable(path),
                        modified_timestamp=stat.st_mtime,
                    )
                )
        self.files = entries

    def open_file(self, target: Path) -> None:
        path = Path(target)
        self.current_file = path
        text = path.read_text()
        self.content_lines = text.splitlines()
        if text.endswith("\n"):
            self.content_lines.append("")
        if not self.content_lines:
            self.content_lines = [""]
        self.scroll_offset = 0
        self.cursor_line = 0
        self.cursor_col = 0
        self.is_editing = False
        self.is_modified = False

    # ------------------------------------------------------------------
    def handle_key(self, key: int) -> bool:
        if key == KEY_UP:
            if self.scroll_offset > 0:
                self.scroll_offset -= 1
            return True
        if key == KEY_DOWN:
            if self.content_lines:
                limit = max(0, len(self.content_lines) - 1)
                self.scroll_offset = min(self.scroll_offset + 1, limit)
            return True
        if key in (ord("e"), ord("E")):
            if self.current_file is None:
                return False
            info = next((f for f in self.files if f.path == self.current_file), None)
            if info and info.is_readonly:
                self.interaction.notify("File is read-only")
                return False
            self.is_editing = not self.is_editing
            if self.is_editing:
                self.cursor_line = 0
                self.cursor_col = 0
            return True
        if key == CTRL_S and self.is_editing and self.current_file:
            self.current_file.write_text("\n".join(self.content_lines))
            self.is_modified = False
            self.interaction.notify("File saved")
            return True
        if key == KEY_ESC and self.is_editing:
            if self.is_modified:
                if not self.interaction.confirm("Discard changes?"):
                    return False
                self.open_file(self.current_file)
            self.is_editing = False
            return True
        if self.is_editing and 32 <= key <= 126 and self.content_lines:
            line = self.content_lines[self.cursor_line]
            char = chr(key)
            before = line[: self.cursor_col]
            after = line[self.cursor_col :]
            self.content_lines[self.cursor_line] = before + char + after
            self.cursor_col += 1
            self.is_modified = True
            return True
        return False

    # ------------------------------------------------------------------
    def render(self, screen, theme) -> None:
        safe_addstr(screen, 0, 0, "Code Viewer", theme.get("highlight"))
        if not self.current_file:
            safe_addstr(screen, 2, 0, "Select a file to view.")
            return

        safe_addstr(screen, 1, 0, f"File: {self.current_file}")
        for idx, line in enumerate(self.content_lines[self.scroll_offset : self.scroll_offset + 40]):
            safe_addstr(screen, 2 + idx, 0, line)


def os_access_writable(path: Path) -> bool:
    """Utility function to detect read-only files without importing os at module level."""
    try:
        return path.stat().st_mode & 0o200 != 0
    except OSError:
        return False
