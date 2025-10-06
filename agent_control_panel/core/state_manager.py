"""State management and persistence."""

import json
import logging
import shutil
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


class StateManager:
    """Manages application state with persistence and undo/redo."""

    def __init__(
        self,
        state_file: Optional[Path] = None,
        max_history: int = 50,
        create_backups: bool = False,
    ):
        """Initialize state manager.

        Args:
            state_file: Path to state file (default: ~/.agent_cli/state.json)
            max_history: Maximum undo/redo history size
            create_backups: Whether to create backups before save
        """
        self.state_file = state_file or (Path.home() / ".agent_cli" / "state.json")
        self.max_history = max_history
        self.create_backups = create_backups

        # Current state
        self._state: Dict[str, Any] = {}

        # History for undo/redo
        self._history: List[Dict[str, Any]] = []
        self._history_index = -1

        # Watchers
        self._watchers: Dict[str, List[Callable]] = {}

        # Thread safety
        self._lock = threading.Lock()

        # Load existing state
        self._load()

    def _load(self) -> None:
        """Load state from disk."""
        if not self.state_file.exists():
            logger.debug(f"State file not found: {self.state_file}")
            return

        try:
            with open(self.state_file) as f:
                self._state = json.load(f)
                logger.info(f"Loaded state from {self.state_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in state file: {e}")
            self._state = {}
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            self._state = {}

    def save(self) -> None:
        """Save state to disk atomically."""
        with self._lock:
            try:
                # Create backup if requested
                if self.create_backups and self.state_file.exists():
                    backup_file = self.state_file.with_suffix(".json.bak")
                    shutil.copy2(self.state_file, backup_file)

                # Ensure directory exists
                self.state_file.parent.mkdir(parents=True, exist_ok=True)

                # Write to temporary file first
                temp_file = self.state_file.with_suffix(".tmp")
                with open(temp_file, "w") as f:
                    json.dump(self._state, f, indent=2)

                # Atomic rename
                temp_file.replace(self.state_file)

                logger.debug(f"Saved state to {self.state_file}")

            except Exception as e:
                logger.error(f"Error saving state: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from state.

        Args:
            key: State key (supports dot notation for nested keys)
            default: Default value if key doesn't exist

        Returns:
            Value from state or default
        """
        with self._lock:
            # Support nested keys with dot notation
            if "." in key:
                parts = key.split(".")
                value = self._state
                for part in parts:
                    if not isinstance(value, dict) or part not in value:
                        return default
                    value = value[part]
                return value
            else:
                return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in state.

        Args:
            key: State key (supports dot notation for nested keys)
            value: Value to set
        """
        with self._lock:
            old_value = self.get(key)

            # Support nested keys with dot notation
            if "." in key:
                parts = key.split(".")
                current = self._state
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                self._state[key] = value

            # Add to history
            self._add_to_history()

            # Notify watchers
            self._notify_watchers(key, old_value, value)

    def _add_to_history(self) -> None:
        """Add current state to history."""
        # Remove any redo history
        self._history = self._history[:self._history_index + 1]

        # Add current state
        self._history.append(self._state.copy())

        # Limit history size
        if len(self._history) > self.max_history:
            self._history.pop(0)
        else:
            self._history_index += 1

    def can_undo(self) -> bool:
        """Check if undo is available.

        Returns:
            True if can undo
        """
        with self._lock:
            return self._history_index > 0

    def undo(self) -> bool:
        """Undo last change.

        Returns:
            True if undo succeeded
        """
        with self._lock:
            if not self.can_undo():
                return False

            self._history_index -= 1
            self._state = self._history[self._history_index].copy()
            logger.debug(f"Undo to history index {self._history_index}")
            return True

    def can_redo(self) -> bool:
        """Check if redo is available.

        Returns:
            True if can redo
        """
        with self._lock:
            return self._history_index < len(self._history) - 1

    def redo(self) -> bool:
        """Redo last undone change.

        Returns:
            True if redo succeeded
        """
        with self._lock:
            if not self.can_redo():
                return False

            self._history_index += 1
            self._state = self._history[self._history_index].copy()
            logger.debug(f"Redo to history index {self._history_index}")
            return True

    def clear(self) -> None:
        """Clear all state."""
        with self._lock:
            self._state = {}
            self._add_to_history()
            logger.debug("State cleared")

    def export(self, export_file: Path) -> None:
        """Export state to a file.

        Args:
            export_file: Path to export to
        """
        with self._lock:
            export_file.parent.mkdir(parents=True, exist_ok=True)
            with open(export_file, "w") as f:
                json.dump(self._state, f, indent=2)
            logger.info(f"Exported state to {export_file}")

    def import_from(self, import_file: Path) -> None:
        """Import state from a file.

        Args:
            import_file: Path to import from
        """
        with self._lock:
            try:
                with open(import_file) as f:
                    imported_state = json.load(f)
                    self._state.update(imported_state)
                    self._add_to_history()
                    logger.info(f"Imported state from {import_file}")
            except Exception as e:
                logger.error(f"Error importing state: {e}")

    def watch(self, key: str, callback: Callable[[Any, Any], None]) -> None:
        """Watch a key for changes.

        Args:
            key: Key to watch
            callback: Function to call with (old_value, new_value)
        """
        with self._lock:
            if key not in self._watchers:
                self._watchers[key] = []
            self._watchers[key].append(callback)
            logger.debug(f"Added watcher for key: {key}")

    def _notify_watchers(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify watchers of a key change.

        Args:
            key: Key that changed
            old_value: Previous value
            new_value: New value
        """
        if key in self._watchers:
            for callback in self._watchers[key]:
                try:
                    callback(old_value, new_value)
                except Exception as e:
                    logger.error(f"Error in watcher callback: {e}")
