"""Model configuration panel."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from agent_cli.models import ModelConfig
from agent_cli.panels.base import Panel
from agent_cli.theme import ThemeManager

KEY_UP = 259
KEY_DOWN = 258
KEY_LEFT = 260
KEY_RIGHT = 261
KEY_ENTER = 10

_DEFAULT_MODELS = [
    {"name": "gpt-4", "label": "GPT-4 32K", "provider": "openai"},
    {"name": "claude-2", "label": "Claude 2 100K", "provider": "anthropic"},
    {"name": "llama-2", "label": "Local Llama-2 13B", "provider": "local"},
]
_PARAMETERS = ["temperature", "max_tokens", "top_p"]


class ModelConfigPanel(Panel):
    """Allow operators to inspect and adjust model settings."""

    def __init__(self, *, config_path: Path) -> None:
        super().__init__(panel_id="config", title="Model Config")
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.models: List[Dict[str, str]] = list(_DEFAULT_MODELS)
        self.selected_model_index = 0
        self.selected_model = self.models[0]["name"]
        self.config = ModelConfig(name=self.selected_model, provider=self.models[0]["provider"])
        self.cursor_index = 0  # 0..len(models)+len(parameters)-1

        self._load()

    # ------------------------------------------------------------------
    def handle_key(self, key: int) -> bool:
        if key == KEY_UP:
            if self.cursor_index == 0:
                return False
            self.cursor_index -= 1
            self.mark_dirty()
            return True
        if key == KEY_DOWN:
            max_index = len(self.models) + len(_PARAMETERS) - 1
            if self.cursor_index >= max_index:
                return False
            self.cursor_index += 1
            self.mark_dirty()
            return True
        if key == KEY_ENTER:
            return self._commit_selection()
        if key == KEY_LEFT:
            return self._adjust_parameter(-1)
        if key == KEY_RIGHT:
            return self._adjust_parameter(1)
        if key in (ord("R"), ord("r")):
            self._reset_defaults()
            return True
        return False

    def render(self, screen, theme: ThemeManager) -> None:  # type: ignore[override]
        screen.addstr(3, 2, "Available Models:")
        for index, model in enumerate(self.models):
            indicator = "●" if model["name"] == self.selected_model else "○"
            cursor = "→" if index == self.cursor_index else " "
            line = f"{cursor} {indicator} {model['label']}"
            screen.addstr(5 + index, 2, line[: 76])

        base = len(self.models)
        screen.addstr(5 + base + 1, 2, "Parameters:")
        for offset, param in enumerate(_PARAMETERS):
            cursor = "→" if self.cursor_index == base + offset else " "
            value = getattr(self.config, param)
            label = f"{param.replace('_', ' ').title():<12}: {value}"
            screen.addstr(7 + base + offset, 2, f"{cursor} {label}"[: 76])

        screen.addstr(
            20,
            2,
            "Enter select model | ←/→ adjust | R reset defaults"[: 76],
        )

    def footer(self) -> str:
        return "↑/↓ move | Enter select | ←/→ adjust params | R reset"

    def capture_state(self) -> Dict:
        return {
            "selected_model": self.selected_model,
            "cursor_index": self.cursor_index,
            "config": {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
            },
        }

    def restore_state(self, state: Dict) -> None:
        model = state.get("selected_model")
        if model and any(item["name"] == model for item in self.models):
            self.selected_model = model
            self.selected_model_index = next(
                i for i, item in enumerate(self.models) if item["name"] == model
            )
        self.cursor_index = int(state.get("cursor_index", 0))
        cfg = state.get("config", {})
        self.config = ModelConfig(
            name=self.selected_model,
            provider=self._provider_for(self.selected_model),
            temperature=float(cfg.get("temperature", 0.7)),
            max_tokens=int(cfg.get("max_tokens", 2048)),
            top_p=float(cfg.get("top_p", 0.95)),
        )
        self.mark_dirty()

    # ------------------------------------------------------------------
    def _commit_selection(self) -> bool:
        if self.cursor_index >= len(self.models):
            return False
        if self.cursor_index == self.selected_model_index:
            return False
        self.selected_model_index = self.cursor_index
        model = self.models[self.selected_model_index]
        self.selected_model = model["name"]
        self.config = ModelConfig(
            name=model["name"],
            provider=model["provider"],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
        )
        self._persist()
        self.mark_dirty()
        return True

    def _adjust_parameter(self, direction: int) -> bool:
        base_index = len(self.models)
        if self.cursor_index < base_index:
            return False
        param = _PARAMETERS[self.cursor_index - base_index]
        old_value = getattr(self.config, param)
        if param == "temperature":
            new_value = min(1.0, max(0.0, round(old_value + 0.05 * direction, 2)))
        elif param == "max_tokens":
            new_value = max(128, min(32768, old_value + 128 * direction))
        else:  # top_p
            new_value = min(1.0, max(0.1, round(old_value + 0.05 * direction, 2)))
        if new_value == old_value:
            return False
        self.config = ModelConfig(
            name=self.config.name,
            provider=self.config.provider,
            temperature=new_value if param == "temperature" else self.config.temperature,
            max_tokens=new_value if param == "max_tokens" else self.config.max_tokens,
            top_p=new_value if param == "top_p" else self.config.top_p,
        )
        self._persist()
        self.mark_dirty()
        return True

    def _reset_defaults(self) -> None:
        provider = self._provider_for(self.selected_model)
        self.config = ModelConfig(name=self.selected_model, provider=provider)
        self._persist()
        self.mark_dirty()

    def _load(self) -> None:
        if not self.config_path.exists():
            self._persist()
            return
        try:
            payload = json.loads(self.config_path.read_text())
        except json.JSONDecodeError:
            self._persist()
            return
        selected = payload.get("selected_model")
        if selected and any(item["name"] == selected for item in self.models):
            self.selected_model = selected
            self.selected_model_index = next(
                i for i, item in enumerate(self.models) if item["name"] == selected
            )
        cfg = payload.get("config", {})
        self.config = ModelConfig(
            name=self.selected_model,
            provider=self._provider_for(self.selected_model),
            temperature=float(cfg.get("temperature", 0.7)),
            max_tokens=int(cfg.get("max_tokens", 2048)),
            top_p=float(cfg.get("top_p", 0.95)),
        )

    def _persist(self) -> None:
        data = {
            "selected_model": self.selected_model,
            "config": {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
            },
        }
        self.config_path.write_text(json.dumps(data, indent=2))

    def _provider_for(self, model_name: str) -> str:
        for model in self.models:
            if model["name"] == model_name:
                return model["provider"]
        return "unknown"


__all__ = [
    "ModelConfigPanel",
    "KEY_UP",
    "KEY_DOWN",
    "KEY_LEFT",
    "KEY_RIGHT",
    "KEY_ENTER",
]
