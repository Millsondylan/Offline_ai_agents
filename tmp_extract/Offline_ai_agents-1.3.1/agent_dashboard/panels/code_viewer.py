"""Code viewer panel."""

import curses
from pathlib import Path

from agent_dashboard.panels.base import BasePanel


class CodeViewerPanel(BasePanel):
    """Code viewing panel."""

    def __init__(self, agent_manager, theme_manager):
        super().__init__("Code Viewer", agent_manager, theme_manager)
        self.current_dir = Path.cwd()
        self.files = []
        self.file_content = []
        self.viewing_file = False
        self.refresh_files()

    def refresh_files(self):
        """Refresh file list."""
        try:
            # Get all files in current directory
            self.files = sorted([
                f for f in self.current_dir.iterdir()
                if f.is_file() and not f.name.startswith('.')
            ])
        except Exception:
            self.files = []

    def render(self, win, start_y: int, start_x: int, height: int, width: int):
        """Render code viewer."""
        y = start_y + 1
        x = start_x + 2

        if self.viewing_file and self.file_content:
            # Show file content
            self.safe_addstr(win, y, x, f"File: {self.files[self.selected_index].name}",
                           self.theme_manager.get('highlight'))
            y += 2

            # Show file lines
            visible_lines = self.file_content[self.scroll_offset:]
            for i, line in enumerate(visible_lines):
                if y >= start_y + height - 2:
                    break
                line_num = self.scroll_offset + i + 1
                text = f"{line_num:4} │ {line}"
                self.safe_addstr(win, y, x, text[:width-4])
                y += 1

            # Instructions
            status_y = start_y + height - 1
            self.safe_addstr(win, status_y, x, "[ESC = Back to list | ↑/↓ = Scroll]",
                           self.theme_manager.get('info'))
        else:
            # Show file list
            self.safe_addstr(win, y, x, f"Directory: {self.current_dir}",
                           self.theme_manager.get('highlight'))
            y += 2

            if not self.files:
                self.safe_addstr(win, y, x, "No files in current directory",
                               self.theme_manager.get('warning'))
            else:
                # Show files
                visible_files = self.files[self.scroll_offset:]
                for i, file in enumerate(visible_files):
                    if y >= start_y + height - 2:
                        break

                    idx = self.scroll_offset + i
                    attr = self.theme_manager.get('selected') if idx == self.selected_index else curses.A_NORMAL

                    prefix = "→ " if idx == self.selected_index else "  "
                    self.safe_addstr(win, y, x, f"{prefix}{file.name}", attr)
                    y += 1

            # Instructions
            status_y = start_y + height - 1
            self.safe_addstr(win, status_y, x, "[Enter = View | R = Refresh | ↑/↓ = Navigate]",
                           self.theme_manager.get('info'))

    def handle_key(self, key: int) -> bool:
        """Handle code viewer keys."""
        if self.viewing_file:
            # File viewing mode
            if key == 27:  # ESC
                self.viewing_file = False
                self.file_content = []
                self.scroll_offset = 0
                return True
            elif key == curses.KEY_UP:
                self.scroll_offset = max(0, self.scroll_offset - 1)
                return True
            elif key == curses.KEY_DOWN:
                self.scroll_offset = min(len(self.file_content) - 1, self.scroll_offset + 1)
                return True
        else:
            # File list mode
            if key == curses.KEY_UP:
                self.selected_index = max(0, self.selected_index - 1)
                return True
            elif key == curses.KEY_DOWN:
                self.selected_index = min(len(self.files) - 1, self.selected_index + 1)
                return True
            elif key in (10, 13, curses.KEY_ENTER):  # Enter
                if self.files and 0 <= self.selected_index < len(self.files):
                    self.open_file(self.files[self.selected_index])
                return True
            elif key in (ord('r'), ord('R')):
                self.refresh_files()
                self.selected_index = 0
                return True

        return False

    def open_file(self, filepath: Path):
        """Open and read a file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self.file_content = f.read().splitlines()
            self.viewing_file = True
            self.scroll_offset = 0
        except Exception:
            self.file_content = ["Error: Could not read file"]
            self.viewing_file = True
