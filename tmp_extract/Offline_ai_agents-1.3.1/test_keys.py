#!/usr/bin/env python3
"""Simple key test to verify keyboard input is working."""

from textual import events
from textual.app import App
from textual.widgets import Static


class KeyTest(App):
    """Test keyboard input."""

    def compose(self):
        yield Static("Press keys (ESC to quit):", id="status")

    async def on_key(self, event: events.Key) -> None:
        """Show what key was pressed."""
        status = self.query_one("#status", Static)
        status.update(f"Key pressed: {event.key!r} (ESC to quit)")
        if event.key == "escape":
            self.exit()


if __name__ == "__main__":
    KeyTest().run()
