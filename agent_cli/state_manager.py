"""Persistence helpers for panel state and undo/redo history."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class _History:
    undo: List[Dict] = field(default_factory=list)
    redo: List[Dict] = field(default_factory=list)


class StateManager:
    """Stores per-panel UI state on disk (optionally) and in memory."""

    def __init__(self, *, base_path: Optional[Path]) -> None:
        self.base_path = Path(base_path) if base_path else None
        self._memory_state: Dict[str, Dict] = {}
        self._history: Dict[str, _History] = {}

        if self.base_path:
            self.base_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _state_path(self, panel_id: str) -> Optional[Path]:
        if not self.base_path:
            return None
        return self.base_path / f"panel_state_{panel_id}.json"

    def save_panel_state(self, panel_id: str, state: Dict) -> None:
        """Persist state to disk or memory."""
        snapshot = dict(state)
        path = self._state_path(panel_id)
        if path:
            try:
                path.write_text(json.dumps(snapshot, indent=2))
            except OSError:
                # Fall back to in-memory storage if disk write fails.
                self._memory_state[panel_id] = snapshot
        else:
            self._memory_state[panel_id] = snapshot

    def load_panel_state(self, panel_id: str) -> Dict:
        path = self._state_path(panel_id)
        if path and path.exists():
            try:
                return json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                return {}
        return dict(self._memory_state.get(panel_id, {}))

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------
    def record_action(self, panel_id: str, state: Dict) -> None:
        history = self._history.setdefault(panel_id, _History())
        history.undo.append(dict(state))
        # Clearing redo because a new action invalidates redo history.
        history.redo.clear()

    def undo(self, panel_id: str) -> Optional[Dict]:
        history = self._history.get(panel_id)
        if not history or len(history.undo) <= 1:
            return None
        current = history.undo.pop()
        history.redo.append(current)
        return dict(history.undo[-1])

    def redo(self, panel_id: str) -> Optional[Dict]:
        history = self._history.get(panel_id)
        if not history or not history.redo:
            return None
        next_state = history.redo.pop()
        history.undo.append(next_state)
        return dict(next_state)

