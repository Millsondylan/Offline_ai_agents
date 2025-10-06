"""Model selection and configuration widget."""
from __future__ import annotations

from typing import List, Optional

from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Label, Button, Input, Select


class ModelSelector(Static):
    """Widget for selecting and configuring AI models."""

    def __init__(self) -> None:
        super().__init__(id="model-selector")
        self.title = Label("═══ MODEL CONFIGURATION ═══", classes="panel-title")
        self.current_model_label = Label("Current Model: --", id="current-model-label")
        self.model_type_label = Label("Type: --", id="model-type-label")

        # Available models
        self.available_models: List[str] = []
        self.current_model: Optional[str] = None
        self.model_type: str = "offline"  # offline, api, custom

    def compose(self):
        yield self.title
        yield self.current_model_label
        yield self.model_type_label

        # Model selection section
        yield Label("\nAvailable Models:", classes="section-label")
        yield Vertical(id="model-list")

        # API key configuration
        yield Label("\nAPI Configuration:", classes="section-label")
        with Horizontal(id="api-config"):
            yield Input(placeholder="API Key (if needed)", password=True, id="api-key-input")
            yield Button("Save API Key", id="save-api-key-btn")

        # Model download section
        yield Label("\nDownload Models:", classes="section-label")
        with Horizontal(id="download-section"):
            yield Input(placeholder="Model name to download", id="download-model-input")
            yield Button("Download", id="download-model-btn")

        # Status
        yield Label("", id="model-status")

    def update_models(self, models: List[str], current: Optional[str] = None) -> None:
        """Update available models list."""
        self.available_models = models
        self.current_model = current or (models[0] if models else None)

        self.current_model_label.update(f"Current Model: {self.current_model or '--'}")

        # Update model list
        model_list = self.query_one("#model-list", Vertical)
        model_list.remove_children()

        for model in models:
            is_current = model == self.current_model
            btn = Button(
                f"{'→' if is_current else ' '} {model}",
                id=f"select-model-{model}",
                classes="model-select-btn" + (" current" if is_current else ""),
            )
            model_list.mount(btn)

    def set_model_type(self, model_type: str) -> None:
        """Set the type of model (offline/api/custom)."""
        self.model_type = model_type
        self.model_type_label.update(f"Type: {model_type}")

        # Show/hide API config based on type
        api_config = self.query_one("#api-config", Horizontal)
        if model_type == "api":
            api_config.display = True
        else:
            api_config.display = False

    def show_status(self, message: str, is_error: bool = False) -> None:
        """Show status message."""
        status = self.query_one("#model-status", Label)
        color = "red" if is_error else "green"
        status.update(f"[bold {color}]{message}[/bold {color}]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "save-api-key-btn":
            self._save_api_key()
        elif button_id == "download-model-btn":
            self._download_model()
        elif button_id and button_id.startswith("select-model-"):
            model_name = button_id.replace("select-model-", "")
            self._select_model(model_name)

    def _save_api_key(self) -> None:
        """Save API key."""
        api_input = self.query_one("#api-key-input", Input)
        api_key = api_input.value.strip()

        if not api_key:
            self.show_status("Please enter an API key", is_error=True)
            return

        # Save to keystore
        from agent.providers.keys import KeyStore
        keystore = KeyStore()

        # Determine provider from current model
        provider_name = "openai"  # Default
        if self.current_model:
            if "claude" in self.current_model.lower():
                provider_name = "anthropic"
            elif "gemini" in self.current_model.lower():
                provider_name = "google"
            elif "gpt" in self.current_model.lower():
                provider_name = "openai"

        keystore.set(provider_name, api_key)
        self.show_status(f"API key saved for {provider_name}")

        # Clear input
        api_input.value = ""

    def _download_model(self) -> None:
        """Download a model (for offline models like Ollama)."""
        download_input = self.query_one("#download-model-input", Input)
        model_name = download_input.value.strip()

        if not model_name:
            self.show_status("Please enter a model name", is_error=True)
            return

        self.show_status(f"Downloading {model_name}... (this may take a while)")

        # Trigger download via app
        if hasattr(self.app, "download_model"):
            self.app.download_model(model_name)
        else:
            # Fallback: try to download with ollama
            import subprocess
            try:
                subprocess.Popen(["ollama", "pull", model_name])
                self.show_status(f"Download started for {model_name}")
                download_input.value = ""
            except Exception as e:
                self.show_status(f"Download failed: {e}", is_error=True)

    def _select_model(self, model_name: str) -> None:
        """Select a model."""
        self.current_model = model_name
        self.update_models(self.available_models, model_name)

        # Notify app
        if hasattr(self.app, "switch_model"):
            self.app.switch_model(model_name)

        self.show_status(f"Switched to {model_name}")
