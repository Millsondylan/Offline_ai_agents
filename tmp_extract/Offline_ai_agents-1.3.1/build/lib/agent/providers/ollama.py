from __future__ import annotations

import json
import shutil
import subprocess
from typing import Dict, Iterable, List

from .base import ModelInfo, ProviderError
from .command import CommandProvider


class OllamaProvider(CommandProvider):
    """Specialised command provider for Ollama local models."""

    name = "ollama"
    mode = "offline"

    def __init__(self, config: Dict | None = None) -> None:
        cfg = dict(config or {})
        cfg.setdefault("args", ["ollama", "run"])
        cfg.setdefault("timeout", 1200)
        cfg.setdefault("model_flag", [])
        super().__init__(cfg)
        if not shutil.which("ollama"):
            raise ProviderError("ollama CLI not found on PATH")
        if not self.current_model():
            self.set_model(cfg.get("default_model", "llama3"))

    def list_models(self) -> Iterable[ModelInfo]:
        payload = self._list_json()
        if not payload:
            return []
        models: List[ModelInfo] = []
        for entry in payload:
            if isinstance(entry, dict):
                name = entry.get("name")
                if not name:
                    continue
                models.append(ModelInfo(name=name, description=entry.get("details")))
            elif isinstance(entry, str):
                models.append(ModelInfo(name=entry))
        return models

    def _list_json(self):  # pragma: no cover - runtime dependent
        commands = [
            ["ollama", "list", "--json"],
            ["ollama", "list", "--format", "json"],
        ]
        for cmd in commands:
            try:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=30,
                )
            except Exception:
                continue
            out = proc.stdout.decode("utf-8", errors="replace").strip()
            if not out:
                continue
            try:
                return json.loads(out)
            except json.JSONDecodeError:
                continue
        return []

    def pull_model(self, model: str) -> None:
        if not model:
            raise ValueError("model name required")
        try:
            subprocess.run(["ollama", "pull", model], check=True, timeout=3600)
        except subprocess.CalledProcessError as exc:  # pragma: no cover - runtime
            raise ProviderError(f"ollama pull failed for {model}") from exc

