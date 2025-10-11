"""Model configuration panel with download and API setup."""

import subprocess
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll, Container
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Button, Input, DataTable, Label, LoadingIndicator, Select
from rich.text import Text

from agent_dashboard.core.model_downloader import ModelDownloader, ProviderInfo


class ModelConfigPanel(Widget):
    """Model configuration panel with Ollama downloads and API setup."""

    DEFAULT_CSS = """
    ModelConfigPanel {
        height: 100%;
        background: $panel;
        border: tall $primary;
    }

    ModelConfigPanel .panel-header {
        height: 3;
        dock: top;
        background: $boost;
        color: $accent;
        text-style: bold;
        content-align: center middle;
        border-bottom: tall $primary;
    }

    ModelConfigPanel .section {
        margin: 1 2;
        padding: 1;
        background: $surface;
        border: tall $primary;
    }

    ModelConfigPanel .section-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    ModelConfigPanel .status-line {
        margin: 0 0 1 0;
        color: $text-muted;
    }

    ModelConfigPanel .success {
        color: $success;
        text-style: bold;
    }

    ModelConfigPanel .error {
        color: $error;
        text-style: bold;
    }

    ModelConfigPanel .warning {
        color: $warning;
        text-style: bold;
    }

    ModelConfigPanel Button {
        margin-right: 1;
        margin-bottom: 1;
    }

    ModelConfigPanel Input {
        width: 100%;
        margin-bottom: 1;
    }

    ModelConfigPanel DataTable {
        height: 15;
        margin-bottom: 1;
    }

    ModelConfigPanel Select {
        width: 100%;
        margin-bottom: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_provider: Optional[ProviderInfo] = None
        self._ollama_models: list[tuple[str, bool]] = []
        self._is_downloading = False

    def compose(self) -> ComposeResult:
        """Compose the model config panel layout."""
        yield Static("MODEL CONFIGURATION", classes="panel-header")

        with VerticalScroll():
            # Current Provider Section
            with Container(classes="section"):
                yield Static("CURRENT PROVIDER", classes="section-title")
                yield Static("", id="current-provider-status", classes="status-line")
                with Horizontal():
                    yield Button("Refresh Status", id="btn-refresh-provider", variant="primary")
                    yield Button("Test Connection", id="btn-test-connection", variant="success")

            # Ollama Models Section
            with Container(classes="section"):
                yield Static("OLLAMA MODELS", classes="section-title")
                yield Static("Local models for offline use", classes="status-line")
                yield DataTable(id="ollama-table", cursor_type="row", zebra_stripes=True)
                with Horizontal():
                    yield Button("Download Selected", id="btn-download-model", variant="success")
                    yield Button("Use Selected", id="btn-use-ollama", variant="primary")
                    yield Button("Refresh List", id="btn-refresh-ollama", variant="default")
                yield Static("", id="ollama-status", classes="status-line")

            # API Configuration Section
            with Container(classes="section"):
                yield Static("API PROVIDERS", classes="section-title")
                yield Static("Configure cloud API providers", classes="status-line")

                yield Label("Provider Type:")
                yield Select(
                    [
                        ("OpenAI (GPT-4)", "openai"),
                        ("Anthropic (Claude)", "anthropic"),
                        ("Google (Gemini)", "gemini"),
                    ],
                    id="api-provider-select",
                    allow_blank=False,
                )

                yield Label("API Key:")
                yield Input(placeholder="Enter API key...", id="api-key-input", password=True)

                yield Label("Model Name (optional):")
                yield Input(placeholder="e.g., gpt-4o-mini, claude-3-5-sonnet", id="api-model-input")

                with Horizontal():
                    yield Button("Save API Config", id="btn-save-api", variant="success")
                    yield Button("Clear API Key", id="btn-clear-api", variant="error")
                yield Static("", id="api-status", classes="status-line")

    def on_mount(self) -> None:
        """Initialize panel when mounted."""
        self._refresh_provider_status()
        self._refresh_ollama_models()

    def _refresh_provider_status(self) -> None:
        """Refresh current provider status."""
        try:
            self._current_provider = ModelDownloader.ensure_provider_configured()
            status_widget = self.query_one("#current-provider-status", Static)

            if self._current_provider:
                provider_text = Text()
                provider_text.append("✓ ", style="bold green")
                provider_text.append(f"Using: {self._current_provider.provider_type}")
                if self._current_provider.model:
                    provider_text.append(f" ({self._current_provider.model})")
                provider_text.append(f" [source: {self._current_provider.source}]", style="dim")
                status_widget.update(provider_text)
            else:
                status_widget.update(Text("✗ No provider configured", style="bold red"))
        except Exception as e:
            status_widget = self.query_one("#current-provider-status", Static)
            status_widget.update(Text(f"Error: {str(e)}", style="bold red"))

    def _refresh_ollama_models(self) -> None:
        """Refresh Ollama models list."""
        try:
            table = self.query_one("#ollama-table", DataTable)
            table.clear(columns=True)
            table.add_columns("Model", "Size", "Status")

            # Check if Ollama is installed
            if not ModelDownloader.check_ollama_installed():
                table.add_row("Ollama not installed", "-", "❌ Not Available")
                status = self.query_one("#ollama-status", Static)
                status.update(Text("Install Ollama: brew install ollama", style="yellow"))
                return

            # Get recommended models and their status
            self._ollama_models = []
            for model in ModelDownloader.RECOMMENDED_MODELS:
                exists = ModelDownloader.check_model_exists(model)
                self._ollama_models.append((model, exists))

                size = self._get_model_size(model)
                status = "✓ Downloaded" if exists else "⬇ Available"
                style = "green bold" if exists else "yellow"

                table.add_row(model, size, Text(status, style=style))

            status_widget = self.query_one("#ollama-status", Static)
            downloaded_count = sum(1 for _, exists in self._ollama_models if exists)
            status_widget.update(f"{downloaded_count}/{len(self._ollama_models)} models downloaded")

        except Exception as e:
            status_widget = self.query_one("#ollama-status", Static)
            status_widget.update(Text(f"Error: {str(e)}", style="bold red"))

    def _get_model_size(self, model: str) -> str:
        """Get approximate model size."""
        size_map = {
            "deepseek-coder:1.3b": "~800MB",
            "deepseek-coder:6.7b": "~4GB",
            "deepseek-coder:6.7b-instruct": "~4GB",
            "deepseek-coder:33b": "~19GB",
        }
        return size_map.get(model, "Unknown")

    def _download_selected_model(self) -> None:
        """Download the selected Ollama model."""
        if self._is_downloading:
            self.app.notify("Download already in progress", severity="warning")
            return

        try:
            table = self.query_one("#ollama-table", DataTable)
            if not table.cursor_row:
                self.app.notify("Please select a model first", severity="warning")
                return

            row_key = table.cursor_row
            row_index = table.get_row_index(row_key)
            model_name, already_exists = self._ollama_models[row_index]

            if already_exists:
                self.app.notify(f"{model_name} already downloaded", severity="information")
                return

            self._is_downloading = True
            status_widget = self.query_one("#ollama-status", Static)
            status_widget.update(Text(f"⬇ Downloading {model_name}... (this may take a few minutes)", style="yellow bold"))

            self.app.notify(f"Downloading {model_name}...", severity="information")

            # Run download in subprocess
            success = ModelDownloader.download_model(model_name)

            self._is_downloading = False

            if success:
                self.app.notify(f"✓ Successfully downloaded {model_name}", severity="information")
                status_widget.update(Text(f"✓ Downloaded {model_name}", style="green bold"))
                self._refresh_ollama_models()
            else:
                self.app.notify(f"✗ Failed to download {model_name}", severity="error")
                status_widget.update(Text(f"✗ Download failed", style="red bold"))

        except Exception as e:
            self._is_downloading = False
            self.app.notify(f"Error downloading model: {str(e)}", severity="error")

    def _use_selected_ollama(self) -> None:
        """Configure agent to use selected Ollama model."""
        try:
            table = self.query_one("#ollama-table", DataTable)
            if not table.cursor_row:
                self.app.notify("Please select a model first", severity="warning")
                return

            row_key = table.cursor_row
            row_index = table.get_row_index(row_key)
            model_name, exists = self._ollama_models[row_index]

            if not exists:
                self.app.notify(f"Model {model_name} not downloaded yet", severity="warning")
                return

            # Configure agent to use this model
            info = ModelDownloader.configure_agent_for_ollama(model_name)
            self._current_provider = info

            self.app.notify(f"✓ Configured to use {model_name}", severity="information")
            self._refresh_provider_status()
            self.post_message(self.ModelChanged(model_name, "ollama"))

        except Exception as e:
            self.app.notify(f"Error configuring model: {str(e)}", severity="error")

    def _save_api_config(self) -> None:
        """Save API configuration."""
        try:
            provider_select = self.query_one("#api-provider-select", Select)
            api_key_input = self.query_one("#api-key-input", Input)
            model_input = self.query_one("#api-model-input", Input)

            provider_type = provider_select.value
            api_key = api_key_input.value.strip()
            model_name = model_input.value.strip()

            if not provider_type:
                self.app.notify("Please select a provider", severity="warning")
                return

            if not api_key:
                self.app.notify("Please enter an API key", severity="warning")
                return

            # Store the API key
            ModelDownloader.store_api_key(provider_type, api_key)

            # Get default model if not specified
            if not model_name:
                entry = next((p for p in ModelDownloader.API_PROVIDERS if p["type"] == provider_type), None)
                model_name = entry["model"] if entry else "default"

            # Configure provider
            config = ModelDownloader._ensure_config()
            provider = config.setdefault("provider", {})
            provider["type"] = provider_type
            provider["model"] = model_name
            ModelDownloader._save_config(config)

            self._current_provider = ProviderInfo(provider_type, model_name, "stored")

            status_widget = self.query_one("#api-status", Static)
            status_widget.update(Text(f"✓ Saved {provider_type} configuration", style="green bold"))

            self.app.notify(f"✓ Configured {provider_type} with API key", severity="information")
            self._refresh_provider_status()
            self.post_message(self.ModelChanged(model_name, provider_type))

            # Clear sensitive input
            api_key_input.value = ""

        except Exception as e:
            self.app.notify(f"Error saving API config: {str(e)}", severity="error")

    def _clear_api_config(self) -> None:
        """Clear API configuration."""
        try:
            provider_select = self.query_one("#api-provider-select", Select)
            provider_type = provider_select.value

            if not provider_type:
                self.app.notify("Please select a provider first", severity="warning")
                return

            # Clear stored key
            keys = ModelDownloader._read_api_keys()
            if provider_type in keys:
                del keys[provider_type]
                ModelDownloader._write_api_keys(keys)

            status_widget = self.query_one("#api-status", Static)
            status_widget.update(Text(f"✓ Cleared {provider_type} API key", style="yellow bold"))

            self.app.notify(f"Cleared {provider_type} API key", severity="information")

        except Exception as e:
            self.app.notify(f"Error clearing API config: {str(e)}", severity="error")

    def _test_connection(self) -> None:
        """Test connection to current provider."""
        try:
            if not self._current_provider:
                self.app.notify("No provider configured", severity="warning")
                return

            status_widget = self.query_one("#current-provider-status", Static)
            status_widget.update(Text("Testing connection...", style="yellow bold"))
            self.app.notify("Testing connection...", severity="information")

            # Test based on provider type
            if self._current_provider.provider_type == "ollama":
                success = self._test_ollama_connection()
            else:
                success = self._test_api_connection()

            if success:
                status_widget.update(Text(f"✓ Connection successful!", style="green bold"))
                self.app.notify("✓ Connection test passed!", severity="information")
            else:
                status_widget.update(Text("✗ Connection failed", style="red bold"))
                self.app.notify("✗ Connection test failed", severity="error")

        except Exception as e:
            self.app.notify(f"Test error: {str(e)}", severity="error")

    def _test_ollama_connection(self) -> bool:
        """Test Ollama connection."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _test_api_connection(self) -> bool:
        """Test API connection (simplified check)."""
        # For now, just verify the key is stored
        if not self._current_provider:
            return False

        stored_key = ModelDownloader.get_stored_api_key(self._current_provider.provider_type)
        return stored_key is not None and len(stored_key) > 10

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "btn-refresh-provider":
            self._refresh_provider_status()
        elif button_id == "btn-test-connection":
            self._test_connection()
        elif button_id == "btn-refresh-ollama":
            self._refresh_ollama_models()
        elif button_id == "btn-download-model":
            self._download_selected_model()
        elif button_id == "btn-use-ollama":
            self._use_selected_ollama()
        elif button_id == "btn-save-api":
            self._save_api_config()
        elif button_id == "btn-clear-api":
            self._clear_api_config()

    class ModelChanged(Message):
        """Message sent when model configuration changes."""

        def __init__(self, model_name: str, provider_type: str) -> None:
            super().__init__()
            self.model_name = model_name
            self.provider_type = provider_type
