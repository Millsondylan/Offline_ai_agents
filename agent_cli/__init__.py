"""Compact TUI-compatible agent dashboard facade.

The real implementation of the dashboard lives under :mod:`agent_dashboard`,
but the test-suite exercises a simplified ``agent_cli`` compatibility layer.
This package exposes light-weight models, panels, controllers and helpers
that mirror the public API expected by the tests.
"""

from __future__ import annotations

__all__ = [
    "theme",
    "models",
    "state_manager",
    "ui_manager",
    "agent_controller",
]

