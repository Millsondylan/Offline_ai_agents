"""Model configuration panel."""

import curses
import os
from pathlib import Path

from agent_dashboard.panels.base import BasePanel


class ModelConfigPanel(BasePanel):
    """Model configuration panel."""

    def __init__(self, agent_manager, theme_manager):
        super().__init__("Model Config", agent_manager, theme_manager)
        self.models = self.discover_models()
        self.selected_model = None

    def discover_models(self):
        """Discover available local models."""
        models = []

        # Check common Ollama models directory
        ollama_dir = Path.home() / ".ollama" / "models"
        if ollama_dir.exists():
            models.append(("Ollama", "Available"))

        # Check for downloaded models
        models_dir = Path.home() / ".cache" / "models"
        if models_dir.exists():
            for model_file in models_dir.glob("*.gguf"):
                models.append((model_file.name, str(model_file)))

        # Environment variables
        if os.getenv("ANTHROPIC_API_KEY"):
            models.append(("Claude (API)", "Configured"))
        if os.getenv("OPENAI_API_KEY"):
            models.append(("OpenAI (API)", "Configured"))

        # Default models
        if not models:
            models = [
                ("No local models found", "Install Ollama or download models"),
                ("API keys not set", "Set ANTHROPIC_API_KEY or OPENAI_API_KEY"),
            ]

        return models

    def render(self, win, start_y: int, start_x: int, height: int, width: int):
        """Render model config."""
        y = start_y + 1
        x = start_x + 2

        self.safe_addstr(win, y, x, "Available Models:",
                       self.theme_manager.get('highlight'))
        y += 2

        # Show models
        visible_models = self.models[self.scroll_offset:]
        for i, (name, status) in enumerate(visible_models):
            if y >= start_y + height - 2:
                break

            idx = self.scroll_offset + i
            attr = self.theme_manager.get('selected') if idx == self.selected_index else curses.A_NORMAL

            prefix = "→ " if idx == self.selected_index else "  "
            text = f"{prefix}{name:30} {status}"
            self.safe_addstr(win, y, x, text[:width-4], attr)
            y += 1

        # Instructions
        status_y = start_y + height - 1
        self.safe_addstr(win, status_y, x, "[Enter = Select | R = Refresh | ↑/↓ = Navigate]",
                       self.theme_manager.get('info'))

    def handle_key(self, key: int) -> bool:
        """Handle model config keys."""
        if key == curses.KEY_UP:
            self.selected_index = max(0, self.selected_index - 1)
            return True
        elif key == curses.KEY_DOWN:
            self.selected_index = min(len(self.models) - 1, self.selected_index + 1)
            return True
        elif key in (10, 13, curses.KEY_ENTER):  # Enter
            if 0 <= self.selected_index < len(self.models):
                self.selected_model = self.models[self.selected_index][0]
                # Update agent state
                self.agent_manager.state.model = self.selected_model
            return True
        elif key in (ord('r'), ord('R')):
            self.models = self.discover_models()
            self.selected_index = 0
            return True

        return False
