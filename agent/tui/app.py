"""Simplified Agent TUI facade for unit testing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from . import test_data_generator
from .navigation import NavEntry


class AgentTUI:
    """Minimal application shell with command helpers."""

    def __init__(self) -> None:
        self.control_root = Path("agent") / "local" / "control"
        self.config_path = Path("agent") / "config.json"
        self._navigation_cache: List[NavEntry] = []

    # ------------------------------------------------------------------
    def _ensure_control_dir(self) -> None:
        self.control_root.mkdir(parents=True, exist_ok=True)

    def _write_command(self, name: str) -> Path:
        self._ensure_control_dir()
        path = self.control_root / f"{name}.cmd"
        path.write_text("")
        return path

    # Command helpers ---------------------------------------------------
    def pause_agent(self) -> None:
        self._write_command("pause")

    def resume_agent(self) -> None:
        self._write_command("resume")

    def stop_agent(self) -> None:
        self._write_command("stop")

    def force_commit(self) -> None:
        self._write_command("commit")

    def apply_all_diffs(self) -> None:
        self._write_command("apply_all_diffs")

    def switch_model(self, model: str) -> None:
        safe_model = model.replace("/", "_")
        self._write_command(f"switch_model_{safe_model}")

    # Config management -------------------------------------------------
    def save_config(self, data: dict) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(data, indent=2))

    # Navigation --------------------------------------------------------
    def _load_navigation_data(self) -> List[dict]:
        data_path = test_data_generator.DATA_PATH
        if not data_path.exists():
            test_data_generator.generate()
        try:
            data = json.loads(data_path.read_text())
        except json.JSONDecodeError:
            data = []
        return data

    def _build_navigation_order(self) -> List[NavEntry]:
        data = self._load_navigation_data()
        if len(data) < 100:
            # Ensure we always have an ample number of entries.
            for idx in range(len(data), 120):
                data.append({"widget_id": f"auto_{idx:03d}", "label": f"Auto Entry {idx:03d}"})
        self._navigation_cache = [NavEntry(item["widget_id"], item["label"]) for item in data]
        return list(self._navigation_cache)

