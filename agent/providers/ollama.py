from __future__ import annotations

import json
import shutil
import subprocess
from typing import Dict, Iterable, List, Optional

from .base import ModelInfo, Provider, ProviderError
from .command import CommandProvider

try:  # pragma: no cover - optional dep
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore


class OllamaProvider(CommandProvider):
    """Specialised provider for Ollama local models.

    Supports both CLI mode (via ollama run command) and HTTP API mode.
    HTTP API mode is preferred when base_url is configured.
    """

    name = "ollama"
    mode = "offline"

    def __init__(self, config: Dict | None = None) -> None:
        cfg = dict(config or {})
        # Set default model from config if provided
        default_model = cfg.get("model") or cfg.get("default_model", "llama3")
        cfg.setdefault("model", default_model)
        cfg.setdefault("args", ["ollama", "run"])
        cfg.setdefault("timeout", 1200)
        cfg.setdefault("model_flag", [])

        # Support HTTP API mode
        self.base_url = cfg.get("base_url", "http://localhost:11434")
        self.use_api = cfg.get("use_api", True)  # Prefer API by default if available

        super().__init__(cfg)

        # Check if ollama CLI is available
        self.has_cli = shutil.which("ollama") is not None

        # If we're in API-only mode and CLI is missing, that's OK
        if not self.has_cli and not self.use_api:
            raise ProviderError("ollama CLI not found on PATH and API mode is disabled")

        # Ensure we have a valid model set
        if not self.current_model():
            self.set_model(default_model)

    def generate_patch(self, prompt: str, cycle_dir: str) -> Optional[str]:
        """Generate patch using HTTP API if available, otherwise fall back to CLI."""
        if self.use_api and requests is not None:
            try:
                return self._generate_via_api(prompt, cycle_dir)
            except Exception as e:
                # Fall back to CLI on API failure if CLI is available
                if self.has_cli:
                    print(f"Ollama API failed, falling back to CLI: {e}")
                else:
                    raise ProviderError(f"Ollama API request failed and no CLI available: {e}")

        # Fall back to CLI mode if available
        if self.has_cli:
            return super().generate_patch(prompt, cycle_dir)
        else:
            raise ProviderError("Cannot generate patch: Ollama CLI not available and API mode disabled")

    def _generate_via_api(self, prompt: str, cycle_dir: str) -> Optional[str]:
        """Generate patch using Ollama HTTP API."""
        import os

        os.makedirs(cycle_dir, exist_ok=True)
        with open(os.path.join(cycle_dir, "prompt.md"), "w", encoding="utf-8") as f:
            f.write(prompt)

        model = self.current_model() or "llama3"
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            output = result.get("response", "")

            with open(os.path.join(cycle_dir, "provider_output.txt"), "w", encoding="utf-8") as f:
                f.write(output)

            return output
        except Exception as exc:
            raise ProviderError(f"Ollama API request failed: {exc}") from exc

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

