"""Model selection and configuration panel."""

from __future__ import annotations

import curses
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

from .base import Panel, safe_addstr

KEY_UP = getattr(curses, "KEY_UP", -1)
KEY_DOWN = getattr(curses, "KEY_DOWN", -2)
KEY_LEFT = getattr(curses, "KEY_LEFT", -3)
KEY_RIGHT = getattr(curses, "KEY_RIGHT", -4)
KEY_ENTER = getattr(curses, "KEY_ENTER", 10)


@dataclass
class ModelConfig:
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.95
    stream: bool = True

    def as_dict(self) -> dict:
        return asdict(self)


class ModelConfigPanel(Panel):
    """Allows operators to switch models and tweak sampling parameters."""

    footer_hint = "Enter select model | ←/→ adjust values | R reset"

    def __init__(self, *, config_path: Path) -> None:
        super().__init__(panel_id="config", title="Model Config")
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.models: List[dict] = [
            {"name": "gpt-4", "description": "Default general model"},
            {"name": "gpt-4o-mini", "description": "Faster, reduced cost"},
            {"name": "deepseek-coder", "description": "Local coding model"},
        ]
        self.cursor_index = 0
        self.selected_model_index = 0
        self.config = ModelConfig()
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self.config_path.exists():
            self._save()
            return
        try:
            data = json.loads(self.config_path.read_text())
        except (OSError, json.JSONDecodeError):
            self._save()
            return
        model_name = data.get("model")
        if model_name:
            for idx, model in enumerate(self.models):
                if model["name"] == model_name:
                    self.selected_model_index = idx
                    break
        config = data.get("config", {})
        self.config = ModelConfig(
            temperature=float(config.get("temperature", 0.7)),
            max_tokens=int(config.get("max_tokens", 2048)),
            top_p=float(config.get("top_p", 0.95)),
            stream=bool(config.get("stream", True)),
        )

    def _save(self) -> None:
        payload = {
            "model": self.selected_model,
            "config": self.config.as_dict(),
        }
        self.config_path.write_text(json.dumps(payload, indent=2))

    # ------------------------------------------------------------------
    @property
    def selected_model(self) -> str:
        return self.models[self.selected_model_index]["name"]

    def handle_key(self, key: int) -> bool:
        if key == KEY_UP:
            self.cursor_index = max(0, self.cursor_index - 1)
            return True
        if key == KEY_DOWN:
            self.cursor_index = min(self.total_rows - 1, self.cursor_index + 1)
            return True
        if key in (KEY_LEFT, KEY_RIGHT):
            step = 1 if key == KEY_RIGHT else -1
            if self.cursor_index == len(self.models):
                self.config.temperature = round(
                    max(0.0, min(1.0, self.config.temperature + step * 0.1)), 2
                )
            elif self.cursor_index == len(self.models) + 1:
                self.config.max_tokens = max(256, self.config.max_tokens + step * 128)
            elif self.cursor_index == len(self.models) + 2:
                self.config.top_p = round(
                    max(0.1, min(1.0, self.config.top_p + step * 0.05)), 2
                )
            else:
                return False
            self._save()
            return True
        if key in (ord("r"), ord("R")):
            self.config = ModelConfig()
            self._save()
            return True
        if key in (KEY_ENTER, 10, 13) and self.cursor_index < len(self.models):
            self.selected_model_index = self.cursor_index
            self._save()
            return True
        return False

    @property
    def total_rows(self) -> int:
        return len(self.models) + 3

    def render(self, screen, theme) -> None:
        safe_addstr(screen, 0, 0, "Model Selection", theme.get("highlight"))
        for idx, model in enumerate(self.models):
            prefix = ">" if idx == self.cursor_index else " "
            marker = "*" if idx == self.selected_model_index else " "
            safe_addstr(
                screen,
                2 + idx,
                0,
                f"{prefix} [{marker}] {model['name']} — {model['description']}",
            )

        config_start = 2 + len(self.models) + 1
        rows = [
            ("Temperature", f"{self.config.temperature:.2f}"),
            ("Max tokens", str(self.config.max_tokens)),
            ("Top-p", f"{self.config.top_p:.2f}"),
        ]
        for offset, (label, value) in enumerate(rows):
            row_index = len(self.models) + offset
            prefix = ">" if self.cursor_index == row_index else " "
            safe_addstr(screen, config_start + offset, 0, f"{prefix} {label}: {value}")

