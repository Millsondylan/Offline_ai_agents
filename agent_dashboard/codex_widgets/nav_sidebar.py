"""Left navigation sidebar with menu options."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Static
from rich.text import Text


class NavSidebar(Widget):
    """Left sidebar navigation menu."""

    DEFAULT_CSS = """
    NavSidebar {
        width: 25;
        dock: left;
        background: $panel;
        border-right: tall $primary;
    }

    NavSidebar VerticalScroll {
        padding: 1 1;
    }

    NavSidebar .nav-title {
        color: $accent;
        text-style: bold;
        padding: 1 0;
        text-align: center;
        background: $boost;
    }

    NavSidebar Button {
        width: 100%;
        height: 3;
        margin: 0 0 1 0;
        border: none;
        background: $surface;
        color: $text;
    }

    NavSidebar Button:hover {
        background: $primary;
        color: $text;
    }

    NavSidebar Button.active {
        background: $accent;
        color: $background;
        text-style: bold;
    }

    NavSidebar .section-header {
        color: $text-muted;
        text-style: bold;
        padding: 1 0 0 1;
        margin-top: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._active_panel = "tasks"

    def compose(self) -> ComposeResult:
        """Compose the navigation sidebar."""
        yield Static("AI AGENT", classes="nav-title")
        with VerticalScroll():
            yield Static("VIEWS", classes="section-header")
            yield Button("Tasks & Goals", id="nav-tasks", classes="active")
            yield Button("AI Thinking", id="nav-thinking")
            yield Button("Logs", id="nav-logs")
            yield Button("Code Viewer", id="nav-code")
            yield Button("Model Config", id="nav-model")
            yield Button("Project Goal", id="nav-goal")

            yield Static("CONTROLS", classes="section-header")
            yield Button("Start Agent", id="control-start", variant="success")
            yield Button("Pause Agent", id="control-pause", variant="primary")
            yield Button("Stop Agent", id="control-stop", variant="error")
            yield Button("Run Tests", id="control-verify", variant="default")

            yield Static("SYSTEM", classes="section-header")
            yield Button("Exit", id="system-exit", variant="error")

    def set_active_panel(self, panel_name: str) -> None:
        """Set the active panel and update button styling."""
        self._active_panel = panel_name

        # Remove active class from all nav buttons
        for button in self.query("Button").filter(lambda btn: btn.id and btn.id.startswith("nav-")):
            button.remove_class("active")

        # Add active class to selected button
        button_id = f"nav-{panel_name}"
        try:
            active_button = self.query_one(f"#{button_id}", Button)
            active_button.add_class("active")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if not button_id:
            return

        if button_id.startswith("nav-"):
            panel_name = button_id.replace("nav-", "")
            self.post_message(self.PanelSelected(panel_name))
        elif button_id.startswith("control-"):
            action = button_id.replace("control-", "")
            self.post_message(self.ControlAction(action))
        elif button_id.startswith("system-"):
            action = button_id.replace("system-", "")
            self.post_message(self.SystemAction(action))

    class PanelSelected(Message):
        """Message sent when a panel is selected."""

        def __init__(self, panel_name: str) -> None:
            super().__init__()
            self.panel_name = panel_name

    class ControlAction(Message):
        """Message sent when a control button is pressed."""

        def __init__(self, action: str) -> None:
            super().__init__()
            self.action = action

    class SystemAction(Message):
        """Message sent when a system button is pressed."""

        def __init__(self, action: str) -> None:
            super().__init__()
            self.action = action
