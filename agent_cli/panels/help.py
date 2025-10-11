"""Keyboard shortcut reference panel."""

from __future__ import annotations

from typing import List, Tuple

from .base import Panel, safe_addstr


class HelpPanel(Panel):
    """Shows navigation shortcuts with a simple search facility."""

    footer_hint = "/ search | ESC close"

    def __init__(self, *, interaction) -> None:
        super().__init__(panel_id="help", title="Help")
        self.interaction = interaction
        self.entries: List[Tuple[str, str]] = [
            ("1. Home", "Overview of the agent state."),
            ("2. Task Manager", "Create and manage tasks."),
            ("3. Stop Agent", "Gracefully stop the agent."),
            ("4. AI Thinking", "Live thought stream."),
            ("5. Logs", "Review execution logs."),
            ("6. Code Editor", "Inspect files."),
            ("7. Model Config", "Choose models."),
            ("8. Verification", "Run checks."),
            ("9. Help", "This screen."),
            ("ESC", "Return to home panel."),
        ]
        self.search_term = ""

    def handle_key(self, key: int) -> bool:
        if key == ord("/"):
            term = self.interaction.prompt_text("Filter help")
            if term is None:
                return False
            self.search_term = term.strip().lower()
            return True
        return False

    def render(self, screen, theme) -> None:
        safe_addstr(screen, 0, 0, "Keyboard Shortcuts", theme.get("highlight"))
        items = (
            [item for item in self.entries if self.search_term in item[0].lower() or self.search_term in item[1].lower()]
            if self.search_term
            else self.entries
        )
        for idx, (shortcut, description) in enumerate(items):
            safe_addstr(screen, 2 + idx, 0, f"{shortcut} — {description}")

