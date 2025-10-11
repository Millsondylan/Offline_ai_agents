"""Code viewer widget with syntax highlighting."""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widget import Widget
from textual.widgets import Static, DirectoryTree, TextArea, Button
from rich.syntax import Syntax
from rich.text import Text


class CodeViewer(Widget):
    """Code viewer with file tree and syntax highlighting."""

    DEFAULT_CSS = """
    CodeViewer {
        height: 100%;
        background: $panel;
        border: tall $primary;
    }

    CodeViewer .viewer-header {
        height: 3;
        dock: top;
        background: $boost;
        color: $accent;
        text-style: bold;
        content-align: center middle;
        border-bottom: tall $primary;
    }

    CodeViewer .content-container {
        height: 1fr;
        layout: horizontal;
    }

    CodeViewer DirectoryTree {
        width: 30%;
        dock: left;
        background: $surface;
        border-right: tall $primary;
    }

    CodeViewer .file-display {
        width: 1fr;
        background: $surface;
        padding: 1;
    }

    CodeViewer .file-info {
        height: 3;
        dock: top;
        background: $boost;
        padding: 0 1;
        content-align: left middle;
        border-bottom: tall $primary;
    }

    CodeViewer .file-content {
        height: 1fr;
        padding: 1;
        overflow-y: auto;
    }

    CodeViewer .controls-row {
        height: auto;
        dock: top;
        padding: 1;
        background: $surface;
        border-bottom: tall $primary;
    }

    CodeViewer Button {
        margin-right: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_file: Path | None = None
        self._root_path = Path.cwd()

    def compose(self) -> ComposeResult:
        """Compose the code viewer layout."""
        yield Static("CODE VIEWER", classes="viewer-header")

        with Horizontal(classes="controls-row"):
            yield Button("Refresh Tree", id="btn-refresh-tree", variant="primary")
            yield Button("Show Agent Files", id="btn-agent-files", variant="default")
            yield Button("Show All Files", id="btn-all-files", variant="default")

        with Horizontal(classes="content-container"):
            yield DirectoryTree(self._root_path, id="file-tree")

            with Vertical(classes="file-display"):
                yield Static("No file selected", id="file-info", classes="file-info")
                yield VerticalScroll(id="file-content-scroll", classes="file-content")

    def on_mount(self) -> None:
        """Initialize when mounted."""
        self._show_welcome_message()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "btn-refresh-tree":
            self._refresh_tree()
        elif button_id == "btn-agent-files":
            self._show_agent_files()
        elif button_id == "btn-all-files":
            self._show_all_files()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection from directory tree."""
        self._load_file(event.path)

    def _refresh_tree(self) -> None:
        """Refresh the directory tree."""
        try:
            tree = self.query_one("#file-tree", DirectoryTree)
            tree.reload()
        except Exception:
            pass

    def _show_agent_files(self) -> None:
        """Switch to showing only agent-related files."""
        agent_path = self._root_path / "agent"
        if agent_path.exists():
            try:
                tree = self.query_one("#file-tree", DirectoryTree)
                tree.path = agent_path
                tree.reload()
            except Exception:
                pass

    def _show_all_files(self) -> None:
        """Switch to showing all files from root."""
        try:
            tree = self.query_one("#file-tree", DirectoryTree)
            tree.path = self._root_path
            tree.reload()
        except Exception:
            pass

    def _show_welcome_message(self) -> None:
        """Show welcome message in file content area."""
        try:
            scroll = self.query_one("#file-content-scroll", VerticalScroll)
            scroll.mount(Static(
                Text(
                    "Select a file from the tree to view its contents.\n\n"
                    "Use the buttons above to navigate:\n"
                    "  • Refresh Tree - Reload the directory tree\n"
                    "  • Show Agent Files - View only agent-related files\n"
                    "  • Show All Files - View all project files",
                    style="dim italic"
                )
            ))
        except Exception:
            pass

    def _load_file(self, file_path: Path) -> None:
        """Load and display a file with syntax highlighting."""
        if not file_path.is_file():
            return

        self._current_file = file_path

        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = file_path.read_text(encoding='latin-1')
            except Exception:
                self._show_error(f"Cannot read file: {file_path.name} (binary or unsupported encoding)")
                return
        except Exception as e:
            self._show_error(f"Error reading file: {str(e)}")
            return

        self._display_file(file_path, content)

    def _display_file(self, file_path: Path, content: str) -> None:
        """Display file content with syntax highlighting."""
        try:
            info_widget = self.query_one("#file-info", Static)
            info_text = Text()
            info_text.append("File: ", style="dim")
            info_text.append(str(file_path.relative_to(self._root_path)), style="bold cyan")
            info_widget.update(info_text)

            scroll = self.query_one("#file-content-scroll", VerticalScroll)
            scroll.remove_children()

            lexer = self._guess_lexer(file_path.name)
            syntax = Syntax(
                content,
                lexer,
                theme="monokai",
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
            )

            scroll.mount(Static(syntax))

        except Exception as e:
            self._show_error(f"Error displaying file: {str(e)}")

    def _show_error(self, message: str) -> None:
        """Show an error message in the content area."""
        try:
            info_widget = self.query_one("#file-info", Static)
            info_widget.update(Text("Error", style="bold red"))

            scroll = self.query_one("#file-content-scroll", VerticalScroll)
            scroll.remove_children()
            scroll.mount(Static(Text(message, style="red italic")))
        except Exception:
            pass

    def _guess_lexer(self, filename: str) -> str:
        """Guess the lexer/language based on file extension."""
        extension = Path(filename).suffix.lower()

        lexer_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.md': 'markdown',
            '.txt': 'text',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.xml': 'xml',
            '.sql': 'sql',
            '.rs': 'rust',
            '.go': 'go',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.dart': 'dart',
            '.r': 'r',
            '.jsonl': 'json',
        }

        return lexer_map.get(extension, 'text')
