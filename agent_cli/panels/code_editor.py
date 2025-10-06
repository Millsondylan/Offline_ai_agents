"""Code editor panel implementation."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Protocol

from agent_cli.models import FileInfo
from agent_cli.panels.base import Panel
from agent_cli.theme import ThemeManager

KEY_UP = 259
KEY_DOWN = 258
KEY_LEFT = 260
KEY_RIGHT = 261
KEY_ENTER = 10
KEY_ESC = 27
CTRL_S = 19
BACKSPACE = 127

_VIEW_LINES = 14


class Interaction(Protocol):
    def prompt_text(self, prompt: str, *, default: str = "", title: str = "") -> Optional[str]:
        ...

    def confirm(self, message: str) -> bool:
        ...

    def notify(self, message: str) -> None:
        ...


def _is_readonly(path: Path) -> bool:
    return not os.access(path, os.W_OK)


class CodeEditorPanel(Panel):
    """Keyboard-driven file browser and editor."""

    def __init__(
        self,
        *,
        root_path: Path,
        interaction: Optional[Interaction] = None,
    ) -> None:
        super().__init__(panel_id="editor", title="Code Editor")
        self.root_path = Path(root_path)
        self.interaction = interaction

        self.files: List[FileInfo] = []
        self.selected_index = 0
        self.current_file: Optional[Path] = None
        self.content_lines: List[str] = []
        self.cursor_line = 0
        self.cursor_col = 0
        self.scroll_offset = 0
        self.is_modified = False
        self.is_editing = False
        self.message: Optional[str] = None

        self._scan_files()

    # ------------------------------------------------------------------
    def _scan_files(self) -> None:
        entries: List[FileInfo] = []
        for path in sorted(self.root_path.glob("**/*")):
            if path.is_file():
                stat = path.stat()
                entries.append(
                    FileInfo(
                        path=path,
                        size=stat.st_size,
                        modified=datetime_from_timestamp(stat.st_mtime),
                        is_readonly=_is_readonly(path),
                    )
                )
        self.files = entries
        if self.selected_index >= len(self.files):
            self.selected_index = max(0, len(self.files) - 1)

    def open_file(self, path: Path) -> None:
        if not path.exists():
            self.message = f"Missing file: {path.name}"
            return
        self.current_file = path
        content = path.read_text(encoding="utf-8", errors="replace")
        self.content_lines = content.splitlines(True) or [""]
        self.cursor_line = 0
        self.cursor_col = 0
        self.scroll_offset = 0
        self.is_modified = False
        self.is_editing = False
        self.message = None
        self.mark_dirty()

    def handle_key(self, key: int) -> bool:
        if self.current_file is None:
            return self._handle_file_list_key(key)
        return self._handle_editor_key(key)

    def _handle_file_list_key(self, key: int) -> bool:
        if not self.files:
            return False
        if key == KEY_UP:
            if self.selected_index == 0:
                return False
            self.selected_index -= 1
            self.mark_dirty()
            return True
        if key == KEY_DOWN:
            if self.selected_index >= len(self.files) - 1:
                return False
            self.selected_index += 1
            self.mark_dirty()
            return True
        if key == KEY_ENTER:
            self.open_file(self.files[self.selected_index].path)
            return True
        return False

    def _handle_editor_key(self, key: int) -> bool:
        if key in (KEY_UP, KEY_DOWN) and not self.is_editing:
            return self._scroll_view(-1 if key == KEY_UP else 1)
        if key == ord("E") or key == ord("e"):
            if self.current_file and _is_readonly(self.current_file):
                self._notify("File is read-only")
                return False
            self.is_editing = True
            self.mark_dirty()
            return True
        if key == CTRL_S:
            return self._save_file()
        if key == KEY_ESC:
            return self._exit_file()
        if not self.is_editing:
            return False
        if key == KEY_UP:
            if self.cursor_line == 0:
                return False
            self.cursor_line -= 1
            self.cursor_col = min(self.cursor_col, len(self.content_lines[self.cursor_line]))
            self._ensure_cursor_visible()
            return True
        if key == KEY_DOWN:
            if self.cursor_line >= len(self.content_lines) - 1:
                return False
            self.cursor_line += 1
            self.cursor_col = min(self.cursor_col, len(self.content_lines[self.cursor_line]))
            self._ensure_cursor_visible()
            return True
        if key == KEY_LEFT:
            if self.cursor_col > 0:
                self.cursor_col -= 1
                return True
            if self.cursor_line > 0:
                self.cursor_line -= 1
                self.cursor_col = max(0, len(self.content_lines[self.cursor_line]) - 1)
                self._ensure_cursor_visible()
                return True
            return False
        if key == KEY_RIGHT:
            line = self.content_lines[self.cursor_line]
            if self.cursor_col < len(line):
                self.cursor_col += 1
                return True
            if self.cursor_line < len(self.content_lines) - 1:
                self.cursor_line += 1
                self.cursor_col = 0
                self._ensure_cursor_visible()
                return True
            return False
        if key == BACKSPACE:
            return self._backspace()
        if key == KEY_ENTER:
            return self._insert_newline()
        if 32 <= key <= 126:
            self._insert_character(chr(key))
            return True
        return False

    def _scroll_view(self, delta: int) -> bool:
        max_offset = max(0, len(self.content_lines) - _VIEW_LINES)
        new_offset = max(0, min(max_offset, self.scroll_offset + delta))
        if new_offset == self.scroll_offset:
            return False
        self.scroll_offset = new_offset
        self.mark_dirty()
        return True

    def _insert_character(self, ch: str) -> None:
        line = self.content_lines[self.cursor_line]
        self.content_lines[self.cursor_line] = (
            line[: self.cursor_col] + ch + line[self.cursor_col :]
        )
        self.cursor_col += len(ch)
        self._set_modified()

    def _insert_newline(self) -> bool:
        line = self.content_lines[self.cursor_line]
        before = line[: self.cursor_col]
        after = line[self.cursor_col :]
        self.content_lines[self.cursor_line] = before + "\n"
        self.content_lines.insert(self.cursor_line + 1, after)
        self.cursor_line += 1
        self.cursor_col = 0
        self._ensure_cursor_visible()
        self._set_modified()
        return True

    def _backspace(self) -> bool:
        if self.cursor_col > 0:
            line = self.content_lines[self.cursor_line]
            self.content_lines[self.cursor_line] = (
                line[: self.cursor_col - 1] + line[self.cursor_col :]
            )
            self.cursor_col -= 1
            self._set_modified()
            return True
        if self.cursor_line == 0:
            return False
        prev_line = self.content_lines[self.cursor_line - 1]
        current_line = self.content_lines.pop(self.cursor_line)
        self.cursor_line -= 1
        self.cursor_col = len(prev_line.rstrip("\n"))
        self.content_lines[self.cursor_line] = prev_line.rstrip("\n") + current_line
        self._ensure_cursor_visible()
        self._set_modified()
        return True

    def _ensure_cursor_visible(self) -> None:
        if self.cursor_line < self.scroll_offset:
            self.scroll_offset = self.cursor_line
        elif self.cursor_line >= self.scroll_offset + _VIEW_LINES:
            self.scroll_offset = self.cursor_line - _VIEW_LINES + 1

    def _save_file(self) -> bool:
        if self.current_file is None or not self.is_editing:
            return False
        if _is_readonly(self.current_file):
            self._notify("Cannot save read-only file")
            return False
        self.current_file.write_text("".join(self.content_lines), encoding="utf-8")
        self.is_modified = False
        self.is_editing = False
        self.message = "Saved"
        self.mark_dirty()
        return True

    def _exit_file(self) -> bool:
        if not self.current_file:
            return False
        if self.is_editing and self.is_modified:
            if self.interaction and not self.interaction.confirm(
                "Discard unsaved changes?"
            ):
                return False
            self.open_file(self.current_file)
        self.current_file = None
        self.is_editing = False
        self.is_modified = False
        self.cursor_line = 0
        self.cursor_col = 0
        self.scroll_offset = 0
        self.message = None
        self.mark_dirty()
        return True

    def render(self, screen, theme: ThemeManager) -> None:  # type: ignore[override]
        if self.current_file is None:
            screen.addstr(3, 2, "Recent Files:")
            for idx, info in enumerate(self.files[: _VIEW_LINES]):
                marker = "→" if idx == self.selected_index else " "
                status = "Read-only" if info.is_readonly else "Writable"
                line = f"{marker} {info.path.name:<30} {info.size:>6} bytes  {status}"
                screen.addstr(5 + idx, 2, line[: 76])
            screen.addstr(20, 2, "Enter: Open | E: Edit | ESC: Back")
            return

        header = f"Editing: {self.current_file.name}"
        if _is_readonly(self.current_file):
            header += " (read-only)"
        screen.addstr(3, 2, header[: 76])
        visible = self.content_lines[self.scroll_offset : self.scroll_offset + _VIEW_LINES]
        for idx, line in enumerate(visible):
            lineno = self.scroll_offset + idx + 1
            prefix = f"{lineno:>4}  "
            screen.addstr(5 + idx, 2, (prefix + line.rstrip("\n"))[: 76])
        footer = "Ctrl+S Save | ESC Exit"
        if self.is_editing:
            footer = "Typing… | Ctrl+S save | ESC cancel"
        screen.addstr(20, 2, footer[: 76])
        if self.message:
            screen.addstr(21, 2, self.message[: 76])

    def footer(self) -> str:
        if self.current_file is None:
            return "Enter open | E edit | ESC back"
        return "Ctrl+S save | ESC exit"

    def capture_state(self) -> Dict:
        state = {
            "selected_index": self.selected_index,
            "scroll_offset": self.scroll_offset,
        }
        if self.current_file:
            state["current_file"] = str(self.current_file)
        return state

    def restore_state(self, state: Dict) -> None:
        self.selected_index = int(state.get("selected_index", 0))
        self.scroll_offset = int(state.get("scroll_offset", 0))
        current = state.get("current_file")
        if current:
            path = Path(current)
            if path.exists():
                self.open_file(path)
        self.mark_dirty()

    def _set_modified(self) -> None:
        self.is_modified = True
        self.mark_dirty()

    def _notify(self, message: str) -> None:
        if self.interaction:
            self.interaction.notify(message)
        self.message = message
        self.mark_dirty()


def datetime_from_timestamp(timestamp: float) -> datetime:
    return datetime.fromtimestamp(timestamp)


__all__ = [
    "CodeEditorPanel",
    "KEY_UP",
    "KEY_DOWN",
    "KEY_LEFT",
    "KEY_RIGHT",
    "KEY_ENTER",
    "KEY_ESC",
    "CTRL_S",
]
