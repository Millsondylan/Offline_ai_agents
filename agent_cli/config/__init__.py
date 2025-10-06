"""Default configuration assets for the agent CLI."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any


def load_default_settings() -> str:
    """Return the bundled default settings JSON as a string."""
    return resources.files(__package__).joinpath("default_settings.json").read_text(encoding="utf-8")


__all__ = ["load_default_settings"]
