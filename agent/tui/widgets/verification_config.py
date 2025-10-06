"""Configuration widget for verification checks."""
from __future__ import annotations

from typing import Dict, List

from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Label, Button, Input, Checkbox


class VerificationConfig(Static):
    """Widget for configuring verification checks and limits."""

    def __init__(self) -> None:
        super().__init__(id="verification-config")
        self.title = Label("═══ VERIFICATION CONFIGURATION ═══", classes="panel-title")
        self.checks_enabled: Dict[str, bool] = {}

    def compose(self):
        yield self.title

        # Global settings
        yield Label("\nGlobal Settings:", classes="section-label")
        with Horizontal(id="global-settings"):
            yield Label("Max Verifications:")
            yield Input(placeholder="100", id="max-verifications-input", value="100")
            yield Label("Max Duration (seconds):")
            yield Input(placeholder="3600", id="max-duration-input", value="3600")

        # Check categories
        yield Label("\nVerification Checks:", classes="section-label")

        # Critical Checks
        yield Label("\n[bold red]CRITICAL CHECKS[/bold red] (Must pass)")
        yield Vertical(id="critical-checks")

        # High Priority Checks
        yield Label("\n[bold yellow]HIGH PRIORITY CHECKS[/bold yellow]")
        yield Vertical(id="high-checks")

        # Medium Priority Checks
        yield Label("\n[bold blue]MEDIUM PRIORITY CHECKS[/bold blue]")
        yield Vertical(id="medium-checks")

        # Low Priority Checks
        yield Label("\n[bold dim]LOW PRIORITY CHECKS[/bold dim]")
        yield Vertical(id="low-checks")

        # Action buttons
        with Horizontal(id="config-actions"):
            yield Button("Apply Configuration", id="apply-config-btn", variant="primary")
            yield Button("Reset to Defaults", id="reset-config-btn")

        yield Label("", id="config-status")

    def load_checks(self, checks: List[Dict]) -> None:
        """Load verification checks into the UI.

        Args:
            checks: List of check definitions with id, name, level, required, enabled
        """
        # Clear existing checks
        for level in ["critical", "high", "medium", "low"]:
            container = self.query_one(f"#{level}-checks", Vertical)
            container.remove_children()

        # Add checks to appropriate categories
        for check in checks:
            level = check.get("level", "medium")
            required = check.get("required", False)
            enabled = check.get("enabled", True)
            check_id = check.get("id", "")
            name = check.get("name", "")
            description = check.get("description", "")

            self.checks_enabled[check_id] = enabled

            # Create checkbox
            checkbox_label = f"{name} - {description}"
            if required:
                checkbox_label += " [REQUIRED]"

            checkbox = Checkbox(
                checkbox_label,
                value=enabled,
                id=f"check-{check_id}",
                disabled=required,  # Can't disable required checks
            )

            # Add to appropriate container
            container_id = f"{level}-checks"
            try:
                container = self.query_one(f"#{container_id}", Vertical)
                container.mount(checkbox)
            except Exception:
                pass  # Container might not exist for this level

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "apply-config-btn":
            self._apply_configuration()
        elif event.button.id == "reset-config-btn":
            self._reset_to_defaults()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        checkbox_id = event.checkbox.id
        if checkbox_id and checkbox_id.startswith("check-"):
            check_id = checkbox_id.replace("check-", "")
            self.checks_enabled[check_id] = event.value

    def _apply_configuration(self) -> None:
        """Apply the current configuration."""
        # Get global settings
        max_verifications_input = self.query_one("#max-verifications-input", Input)
        max_duration_input = self.query_one("#max-duration-input", Input)

        try:
            max_verifications = int(max_verifications_input.value or "100")
            max_duration = int(max_duration_input.value or "3600")
        except ValueError:
            self._show_status("Invalid number format", is_error=True)
            return

        # Collect enabled checks
        enabled_checks = [check_id for check_id, enabled in self.checks_enabled.items() if enabled]

        # Apply via app
        if hasattr(self.app, "configure_verification"):
            self.app.configure_verification(
                max_verifications=max_verifications,
                max_duration=max_duration,
                enabled_checks=enabled_checks,
            )

        self._show_status(f"Configuration applied: {len(enabled_checks)} checks enabled")

    def _reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        # Reset inputs
        max_verifications_input = self.query_one("#max-verifications-input", Input)
        max_duration_input = self.query_one("#max-duration-input", Input)

        max_verifications_input.value = "100"
        max_duration_input.value = "3600"

        # Re-enable all non-required checkboxes
        for check_id in self.checks_enabled.keys():
            self.checks_enabled[check_id] = True
            try:
                checkbox = self.query_one(f"#check-{check_id}", Checkbox)
                if not checkbox.disabled:
                    checkbox.value = True
            except Exception:
                pass

        self._show_status("Reset to default configuration")

    def _show_status(self, message: str, is_error: bool = False) -> None:
        """Show status message."""
        status = self.query_one("#config-status", Label)
        color = "red" if is_error else "green"
        status.update(f"[bold {color}]{message}[/bold {color}]")
