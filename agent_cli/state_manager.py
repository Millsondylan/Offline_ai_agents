"""State persistence utilities for the control panel."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Union


class StateManager:
    """Persist panel state and offer undo/redo stacks."""

    def __init__(self, base_path: Optional[Union[Path, str]]) -> None:
        self._base_path: Optional[Path]
        if base_path is None:
            self._base_path = None
            self._memory_store: Dict[str, Dict] = {}
        else:
            path = Path(base_path)
            path.mkdir(parents=True, exist_ok=True)
            self._base_path = path
            self._memory_store = {}
        self._histories: Dict[str, List[Dict]] = {}
        self._redos: Dict[str, List[Dict]] = {}

    def _panel_state_path(self, panel_id: str) -> Optional[Path]:
        if self._base_path is None:
            return None
        return self._base_path / f"panel_state_{panel_id}.json"

    def save_panel_state(self, panel_id: str, state: Dict) -> None:
        snapshot = deepcopy(state)
        state_path = self._panel_state_path(panel_id)
        if state_path is None:
            self._memory_store[panel_id] = snapshot
        else:
            state_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True))

    def load_panel_state(self, panel_id: str) -> Dict:
        state_path = self._panel_state_path(panel_id)
        if state_path is None:
            return deepcopy(self._memory_store.get(panel_id, {}))
        if not state_path.exists():
            return {}
        try:
            data = json.loads(state_path.read_text())
            if isinstance(data, dict):
                return data
            return {}
        except json.JSONDecodeError:
            return {}

    def record_action(self, key: str, state: Dict) -> None:
        history = self._histories.setdefault(key, [])
        history.append(deepcopy(state))
        self._redos[key] = []

    def undo(self, key: str) -> Optional[Dict]:
        history = self._histories.get(key)
        if not history or len(history) <= 1:
            return None
        redo_stack = self._redos.setdefault(key, [])
        redo_stack.append(history.pop())
        return deepcopy(history[-1])

    def redo(self, key: str) -> Optional[Dict]:
        redo_stack = self._redos.get(key)
        if not redo_stack:
            return None
        state = redo_stack.pop()
        history = self._histories.setdefault(key, [])
        history.append(deepcopy(state))
        return deepcopy(state)


__all__ = ["StateManager"]
