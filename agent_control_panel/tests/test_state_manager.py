"""Tests for StateManager - Phase 2: Agent Integration."""

import json
import pytest
from pathlib import Path


class TestStateManager:
    """Test state persistence and management."""

    def test_state_persistence_to_disk(self, tmp_path):
        """Test state is saved to disk correctly."""
        from agent_control_panel.core.state_manager import StateManager

        state_file = tmp_path / "state.json"
        manager = StateManager(state_file)

        manager.set("test_key", "test_value")
        manager.save()

        assert state_file.exists()
        with open(state_file) as f:
            data = json.load(f)
            assert data["test_key"] == "test_value"

    def test_state_loading_from_disk(self, tmp_path):
        """Test state is loaded from disk correctly."""
        from agent_control_panel.core.state_manager import StateManager

        state_file = tmp_path / "state.json"
        with open(state_file, "w") as f:
            json.dump({"existing_key": "existing_value"}, f)

        manager = StateManager(state_file)
        assert manager.get("existing_key") == "existing_value"

    def test_state_restoration_after_crash(self, tmp_path):
        """Test state can be restored after unexpected shutdown."""
        from agent_control_panel.core.state_manager import StateManager

        state_file = tmp_path / "state.json"

        # Create manager, set state, save
        manager1 = StateManager(state_file)
        manager1.set("scroll_position", 42)
        manager1.set("active_panel", "tasks")
        manager1.save()

        # Simulate crash and restart
        manager2 = StateManager(state_file)
        assert manager2.get("scroll_position") == 42
        assert manager2.get("active_panel") == "tasks"

    def test_undo_operation(self):
        """Test undo reverts to previous state."""
        from agent_control_panel.core.state_manager import StateManager

        manager = StateManager()

        manager.set("counter", 1)
        manager.set("counter", 2)
        manager.set("counter", 3)

        manager.undo()
        assert manager.get("counter") == 2

        manager.undo()
        assert manager.get("counter") == 1

    def test_redo_operation(self):
        """Test redo reapplies undone change."""
        from agent_control_panel.core.state_manager import StateManager

        manager = StateManager()

        manager.set("value", "a")
        manager.set("value", "b")
        manager.undo()

        assert manager.get("value") == "a"

        manager.redo()
        assert manager.get("value") == "b"

    def test_undo_redo_stack_limits(self):
        """Test undo/redo stacks respect size limits."""
        from agent_control_panel.core.state_manager import StateManager

        manager = StateManager(max_history=5)

        # Make more changes than history size
        for i in range(10):
            manager.set("counter", i)

        # Should only be able to undo 5 times
        undo_count = 0
        while manager.can_undo():
            manager.undo()
            undo_count += 1

        assert undo_count == 5

    def test_concurrent_state_updates(self):
        """Test concurrent state updates are handled safely."""
        from agent_control_panel.core.state_manager import StateManager
        import threading

        manager = StateManager()
        errors = []

        def writer(prefix):
            try:
                for i in range(50):
                    manager.set(f"{prefix}_key", i)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer, args=("thread1",)),
            threading.Thread(target=writer, args=("thread2",)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_invalid_state_file_handling(self, tmp_path):
        """Test graceful handling of corrupted state file."""
        from agent_control_panel.core.state_manager import StateManager

        state_file = tmp_path / "state.json"
        with open(state_file, "w") as f:
            f.write("{ invalid json }")

        # Should not crash, should use empty state
        manager = StateManager(state_file)
        assert manager.get("any_key") is None

    def test_missing_state_file_handling(self, tmp_path):
        """Test handling of missing state file."""
        from agent_control_panel.core.state_manager import StateManager

        state_file = tmp_path / "nonexistent.json"
        manager = StateManager(state_file)

        assert manager.get("any_key") is None

    def test_state_backup_creation(self, tmp_path):
        """Test backup is created before overwriting state."""
        from agent_control_panel.core.state_manager import StateManager

        state_file = tmp_path / "state.json"
        manager = StateManager(state_file, create_backups=True)

        manager.set("data", "version1")
        manager.save()

        manager.set("data", "version2")
        manager.save()

        # Should have backup
        backup_file = tmp_path / "state.json.bak"
        assert backup_file.exists()

        with open(backup_file) as f:
            data = json.load(f)
            assert data["data"] == "version1"

    def test_nested_state_keys(self):
        """Test handling of nested state keys."""
        from agent_control_panel.core.state_manager import StateManager

        manager = StateManager()

        manager.set("panel.tasks.scroll", 42)
        manager.set("panel.tasks.selected", 3)

        assert manager.get("panel.tasks.scroll") == 42
        assert manager.get("panel.tasks.selected") == 3

    def test_state_clear_operation(self):
        """Test clearing all state."""
        from agent_control_panel.core.state_manager import StateManager

        manager = StateManager()

        manager.set("key1", "value1")
        manager.set("key2", "value2")

        manager.clear()

        assert manager.get("key1") is None
        assert manager.get("key2") is None

    def test_state_export_import(self, tmp_path):
        """Test exporting and importing state."""
        from agent_control_panel.core.state_manager import StateManager

        export_file = tmp_path / "export.json"

        manager1 = StateManager()
        manager1.set("setting1", "value1")
        manager1.set("setting2", 42)
        manager1.export(export_file)

        manager2 = StateManager()
        manager2.import_from(export_file)

        assert manager2.get("setting1") == "value1"
        assert manager2.get("setting2") == 42

    def test_atomic_save_operation(self, tmp_path):
        """Test state save is atomic (no partial writes)."""
        from agent_control_panel.core.state_manager import StateManager

        state_file = tmp_path / "state.json"
        manager = StateManager(state_file)

        # Add lots of data
        for i in range(1000):
            manager.set(f"key_{i}", f"value_{i}")

        manager.save()

        # File should be valid JSON
        with open(state_file) as f:
            data = json.load(f)
            assert len(data) == 1000

    def test_watch_key_for_changes(self):
        """Test watching a key for changes."""
        from agent_control_panel.core.state_manager import StateManager

        manager = StateManager()
        changes = []

        def callback(old_value, new_value):
            changes.append((old_value, new_value))

        manager.watch("watched_key", callback)

        manager.set("watched_key", "value1")
        manager.set("watched_key", "value2")

        assert len(changes) == 2
        assert changes[0] == (None, "value1")
        assert changes[1] == ("value1", "value2")
