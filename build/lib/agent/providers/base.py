from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence


class ProviderError(RuntimeError):
    """Raised when provider cannot complete a request."""


@dataclass
class ModelInfo:
    name: str
    description: Optional[str] = None
    tags: Optional[Sequence[str]] = None


class Provider(abc.ABC):
    """Base provider contract.

    Providers may run locally (Ollama/manual) or remotely (hosted APIs).
    They are responsible for reading the prompt, producing raw output,
    and optionally exposing model metadata for UI selection.
    """

    name: str = "provider"
    mode: str = "generic"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

    @abc.abstractmethod
    def generate_patch(self, prompt: str, cycle_dir: str) -> Optional[str]:
        """Return provider output (often a diff) or ``None`` if unavailable."""

    def list_models(self) -> Iterable[ModelInfo]:
        """Return available models for selection (empty by default)."""
        return []

    def current_model(self) -> Optional[str]:
        return self.config.get("model")

    def set_model(self, model: str) -> None:
        self.config["model"] = model

    def supports_slash_command(self, command: str) -> bool:
        return False

    def run_slash_command(self, command: str, *args: str) -> str:
        raise ProviderError(f"slash command {command!r} not supported")


def ensure_sequence(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]
