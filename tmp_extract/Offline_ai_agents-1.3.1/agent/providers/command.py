from __future__ import annotations

import os
import subprocess
from typing import Dict, List, Optional

from .base import ModelInfo, Provider, ProviderError, ensure_sequence


class CommandProvider(Provider):
    """Runs a local command (e.g. Ollama) with the prompt on stdin."""

    name = "command"
    mode = "offline"

    def __init__(self, config: Optional[Dict] = None) -> None:
        super().__init__(config)
        self.args: List[str] = ensure_sequence(self.config.get("args") or self.config.get("cmd"))
        if not self.args:
            raise ProviderError("command provider requires non-empty 'args'")
        self.timeout = int(self.config.get("timeout", self.config.get("timeout_seconds", 900)))
        self.env = {**os.environ, **self.config.get("env", {})}
        self.cwd = self.config.get("cwd")
        self.model_flag = tuple(self.config.get("model_flag", []))

    def generate_patch(self, prompt: str, cycle_dir: str) -> Optional[str]:
        os.makedirs(cycle_dir, exist_ok=True)
        with open(os.path.join(cycle_dir, "prompt.md"), "w", encoding="utf-8") as f:
            f.write(prompt)
        cmd = list(self.args)
        model = self.current_model()
        if model and self.model_flag:
            cmd = list(cmd) + list(self.model_flag) + [model]
        try:
            proc = subprocess.run(
                cmd,
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=self.timeout,
                cwd=self.cwd,
                env=self.env,
            )
        except subprocess.TimeoutExpired as exc:  # pragma: no cover - runtime
            raise ProviderError(f"command provider timeout after {self.timeout}s") from exc
        output = proc.stdout.decode("utf-8", errors="replace")
        with open(os.path.join(cycle_dir, "provider_output.txt"), "w", encoding="utf-8") as f:
            f.write(output)
        return output

    def list_models(self):  # pragma: no cover - best effort
        models = self.config.get("models", [])
        return [ModelInfo(name=m) for m in ensure_sequence(models)]
