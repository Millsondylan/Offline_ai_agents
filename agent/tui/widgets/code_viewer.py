"""Code viewer and editor widget."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Label, Button, TextArea, Input


class CodeViewer(Static):
    """View and edit code files."""

    def __init__(self) -> None:
        super().__init__(id="code-viewer")
        self.title = Label("", id="code-viewer-title")
        self.current_file: Optional[Path] = None
        self.original_content: str = ""
        self.modified: bool = False

    def compose(self):
        yield self.title
        with Horizontal(id="code-viewer-toolbar"):
            yield Button("Save", id="code-save-btn", variant="primary")
            yield Button("Revert", id="code-revert-btn")
            yield Button("Close", id="code-close-btn")
            yield Label("", id="code-status")

        yield TextArea(id="code-editor", language="python")

        yield Label("Press ESC to return to menu", id="code-help")

    def load_file(self, file_path: Path) -> bool:
        """Load a file for viewing/editing.

        Args:
            file_path: Path to file

        Returns:
            True if loaded successfully
        """
        try:
            if not file_path.exists():
                self._show_status(f"File not found: {file_path}", error=True)
                return False

            content = file_path.read_text(encoding="utf-8")
            self.current_file = file_path
            self.original_content = content
            self.modified = False

            # Update UI
            self.title.update(f"═══ CODE: {file_path.name} ═══")

            editor = self.query_one("#code-editor", TextArea)
            editor.text = content

            # Detect language
            suffix = file_path.suffix.lower()
            language_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".html": "html",
                ".css": "css",
                ".json": "json",
                ".md": "markdown",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".toml": "toml",
                ".sh": "bash",
            }
            language = language_map.get(suffix, "python")
            editor.language = language

            self._show_status(f"Loaded {file_path.name} ({len(content)} chars)")
            return True

        except Exception as e:
            self._show_status(f"Error loading file: {e}", error=True)
            return False

    def save_file(self) -> bool:
        """Save current file.

        Returns:
            True if saved successfully
        """
        if not self.current_file:
            self._show_status("No file loaded", error=True)
            return False

        try:
            editor = self.query_one("#code-editor", TextArea)
            content = editor.text

            self.current_file.write_text(content, encoding="utf-8")
            self.original_content = content
            self.modified = False

            self._show_status(f"✓ Saved {self.current_file.name}")
            return True

        except Exception as e:
            self._show_status(f"Error saving: {e}", error=True)
            return False

    def revert_changes(self) -> None:
        """Revert to original content."""
        if not self.current_file:
            return

        editor = self.query_one("#code-editor", TextArea)
        editor.text = self.original_content
        self.modified = False
        self._show_status("Reverted to original")

    def close_file(self) -> None:
        """Close current file."""
        if self.modified:
            # TODO: Add confirmation dialog
            pass

        self.current_file = None
        self.original_content = ""
        self.modified = False

        editor = self.query_one("#code-editor", TextArea)
        editor.text = ""

        if hasattr(self.app, "show_menu"):
            self.app.show_menu()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text changes."""
        if self.original_content and event.text_area.id == "code-editor":
            editor = self.query_one("#code-editor", TextArea)
            self.modified = editor.text != self.original_content

            if self.modified:
                self._show_status("● Modified", error=False)
            else:
                self._show_status("No changes", error=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "code-save-btn":
            self.save_file()
        elif button_id == "code-revert-btn":
            self.revert_changes()
        elif button_id == "code-close-btn":
            self.close_file()

    def _show_status(self, message: str, error: bool = False) -> None:
        """Show status message."""
        status = self.query_one("#code-status", Label)
        color = "red" if error else "green"
        status.update(f"[{color}]{message}[/{color}]")


class FileSelector(Static):
    """Select a file to view/edit."""

    def __init__(self) -> None:
        super().__init__(id="file-selector")
        self.title = Label("═══ SELECT FILE ═══", classes="panel-title")

    def compose(self):
        yield self.title
        yield Label("\nEnter file path to view/edit:", classes="section-label")
        with Horizontal(id="file-selector-input"):
            yield Input(placeholder="path/to/file.py", id="file-path-input")
            yield Button("Open", id="file-open-btn", variant="primary")

        yield Label("\nRecent files:", classes="section-label")
        yield Vertical(id="recent-files-list")

        yield Label("", id="file-selector-status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "file-open-btn":
            self._open_file()

    def _open_file(self) -> None:
        """Open the file from input."""
        file_input = self.query_one("#file-path-input", Input)
        file_path = file_input.value.strip()

        if not file_path:
            self._show_status("Enter a file path", error=True)
            return

        path = Path(file_path)
        if not path.exists():
            self._show_status(f"File not found: {file_path}", error=True)
            return

        # Open in code viewer
        if hasattr(self.app, "open_code_viewer"):
            self.app.open_code_viewer(path)
        else:
            self._show_status("Code viewer not available", error=True)

    def _show_status(self, message: str, error: bool = False) -> None:
        """Show status message."""
        status = self.query_one("#file-selector-status", Label)
        color = "red" if error else "green"
        status.update(f"[{color}]{message}[/{color}]")
