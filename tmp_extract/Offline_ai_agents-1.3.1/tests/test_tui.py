"""Comprehensive TUI test suite."""
import json

import pytest
from agent.tui.app import AgentTUI
from agent.tui.navigation import NavEntry, NavigationManager
from agent.tui.state_watcher import StateWatcher


class TestNavigation:
    """Test navigation system."""

    def test_navigation_completeness(self):
        """Test all elements are reachable via arrow keys (nav_01)."""
        # Generate test data first
        import subprocess
        subprocess.run(["python3", "agent/tui/test_data_generator.py"], check=True)

        app = AgentTUI()
        # Build initial navigation
        entries = app._build_navigation_order()

        # Should have 60 tasks + 20 gates + 40+ artifacts + 4 control buttons + 4 tabs + 2 diff actions
        # = 130+ entries
        assert len(entries) >= 100, f"Expected 100+ nav entries, got {len(entries)}"

        # Verify all entries have unique IDs
        widget_ids = [e.widget_id for e in entries]
        assert len(widget_ids) == len(set(widget_ids)), "Duplicate widget IDs found"

    def test_focus_preservation(self):
        """Test focus is preserved during state updates (nav_02)."""
        app = AgentTUI()
        nav = NavigationManager(app)

        # Set initial entries
        entries1 = [
            NavEntry("widget_1", "Action 1"),
            NavEntry("widget_2", "Action 2"),
            NavEntry("widget_3", "Action 3"),
        ]
        nav.set_entries(entries1)
        nav.current_index = 1  # Focus on widget_2

        # Update entries with same widgets
        entries2 = [
            NavEntry("widget_1", "Action 1"),
            NavEntry("widget_2", "Action 2 Updated"),
            NavEntry("widget_3", "Action 3"),
        ]
        nav.set_entries(entries2)

        # Focus should still be on widget_2
        assert nav.current_index == 1
        assert nav.get_focused().widget_id == "widget_2"

    def test_focus_wrap_around(self):
        """Test navigation wraps from bottom to top and vice versa (nav_03)."""
        app = AgentTUI()
        nav = NavigationManager(app)

        entries = [
            NavEntry("widget_1", "Action 1"),
            NavEntry("widget_2", "Action 2"),
            NavEntry("widget_3", "Action 3"),
        ]
        nav.set_entries(entries)

        # Start at 0, go up should wrap to 2
        nav.current_index = 0
        nav.focus_previous()
        assert nav.current_index == 2

        # At 2, go down should wrap to 0
        nav.focus_next()
        assert nav.current_index == 0


class TestCommands:
    """Test command execution."""

    def test_pause_command(self, tmp_path):
        """Test pause button creates correct command file (cmd_01)."""
        app = AgentTUI()
        app.control_root = tmp_path / "control"

        app.pause_agent()

        cmd_file = app.control_root / "pause.cmd"
        assert cmd_file.exists()
        assert cmd_file.read_text() == ""

    def test_resume_command(self, tmp_path):
        """Test resume button creates correct command file (cmd_02)."""
        app = AgentTUI()
        app.control_root = tmp_path / "control"

        app.resume_agent()

        cmd_file = app.control_root / "resume.cmd"
        assert cmd_file.exists()

    def test_stop_command(self, tmp_path):
        """Test stop button creates correct command file (cmd_03)."""
        app = AgentTUI()
        app.control_root = tmp_path / "control"

        app.stop_agent()

        cmd_file = app.control_root / "stop.cmd"
        assert cmd_file.exists()

    def test_force_commit_command(self, tmp_path):
        """Test force commit creates command file (cmd_04)."""
        app = AgentTUI()
        app.control_root = tmp_path / "control"

        app.force_commit()

        cmd_file = app.control_root / "commit.cmd"
        assert cmd_file.exists()

    def test_apply_diffs_command(self, tmp_path):
        """Test apply diffs creates command file (cmd_05)."""
        app = AgentTUI()
        app.control_root = tmp_path / "control"

        app.apply_all_diffs()

        cmd_file = app.control_root / "apply_all_diffs.cmd"
        assert cmd_file.exists()

    def test_model_switch_command(self, tmp_path):
        """Test model switch creates correct command file (cmd_06)."""
        app = AgentTUI()
        app.control_root = tmp_path / "control"

        app.switch_model("gpt-4")

        cmd_file = app.control_root / "switch_model_gpt-4.cmd"
        assert cmd_file.exists()


class TestStateWatcher:
    """Test state watching and polling."""

    def test_state_polling_control(self, tmp_path):
        """Test control state is read correctly (state_01)."""
        watcher = StateWatcher()
        watcher.state_root = tmp_path / "state"
        watcher.config_path = tmp_path / "config.json"
        watcher.state_root.mkdir()

        # Create test session
        session = {
            "status": "running",
            "cycle_count": 42,
            "session_duration": 3600,
            "phase": "testing"
        }
        (watcher.state_root / "session.json").write_text(json.dumps(session))

        # Create test config
        config = {
            "provider": {"type": "openai", "model": "gpt-4"},
            "available_models": ["gpt-4", "gpt-3.5"]
        }
        watcher.config_path.write_text(json.dumps(config))

        snapshot = watcher.snapshot()

        assert snapshot.control.status == "running"
        assert snapshot.control.cycle_count == 42
        assert snapshot.control.provider == "openai"
        assert snapshot.control.model == "gpt-4"
        assert snapshot.control.available_models == ["gpt-4", "gpt-3.5"]

    def test_task_queue_polling(self, tmp_path):
        """Test task queue is read correctly (state_02)."""
        watcher = StateWatcher()
        watcher.state_root = tmp_path / "state"
        watcher.state_root.mkdir()

        # Create scheduler with tasks
        scheduler = {
            "tasks": [
                {"id": "task_1", "name": "Test task 1", "status": "running"},
                {"id": "task_2", "name": "Test task 2", "status": "pending"}
            ]
        }
        (watcher.state_root / "scheduler.json").write_text(json.dumps(scheduler))

        snapshot = watcher.snapshot()

        assert len(snapshot.tasks) == 2
        assert snapshot.tasks[0].id == "task_1"
        assert snapshot.tasks[0].status == "running"
        assert snapshot.tasks[1].id == "task_2"

    def test_gate_polling(self, tmp_path):
        """Test gate status is read correctly (state_03)."""
        watcher = StateWatcher()
        watcher.artifact_root = tmp_path / "artifacts"
        cycle_dir = watcher.artifact_root / "cycle_001"
        cycle_dir.mkdir(parents=True)

        # Create cycle metadata
        meta = {
            "gates": {
                "ruff": {"passed": True, "findings": []},
                "bandit": {"passed": False, "findings": [{"issue": "test"}]}
            }
        }
        (cycle_dir / "cycle.meta.json").write_text(json.dumps(meta))

        snapshot = watcher.snapshot()

        assert len(snapshot.gates) == 2
        assert snapshot.gates[0].name == "ruff"
        assert snapshot.gates[0].status == "passed"
        assert snapshot.gates[1].name == "bandit"
        assert snapshot.gates[1].status == "failed"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_state_handling(self):
        """Test TUI handles empty state gracefully (edge_01)."""
        watcher = StateWatcher()
        snapshot = watcher.snapshot()

        # Should not crash with missing files
        assert snapshot.control.status == "idle"
        assert len(snapshot.tasks) == 0
        assert len(snapshot.gates) == 0

    def test_corrupted_json_handling(self, tmp_path):
        """Test TUI handles corrupted JSON gracefully (edge_02)."""
        watcher = StateWatcher()
        watcher.state_root = tmp_path / "state"
        watcher.state_root.mkdir()

        # Write invalid JSON
        (watcher.state_root / "session.json").write_text("{invalid json")

        snapshot = watcher.snapshot()

        # Should return defaults, not crash
        assert snapshot.control.status == "idle"

    def test_missing_directories(self, tmp_path):
        """Test TUI creates missing directories (edge_03)."""
        app = AgentTUI()
        app.control_root = tmp_path / "control"

        # Directory doesn't exist
        assert not app.control_root.exists()

        # Execute command
        app.pause_agent()

        # Directory should be created
        assert app.control_root.exists()
        assert (app.control_root / "pause.cmd").exists()


class TestConfigEditor:
    """Test config editor functionality."""

    def test_config_loading(self, tmp_path):
        """Test config is loaded and parsed correctly."""
        app = AgentTUI()
        app.config_path = tmp_path / "config.json"

        config = {"key1": "value1", "key2": 42, "nested": {"a": 1}}
        app.config_path.write_text(json.dumps(config))

        watcher = StateWatcher()
        watcher.config_path = app.config_path
        snapshot = watcher.snapshot()

        # Config should be loaded
        output = snapshot.output
        assert "key1" in output.config_text
        assert "value1" in output.config_text

    def test_config_save(self, tmp_path):
        """Test config changes are saved correctly."""
        app = AgentTUI()
        app.config_path = tmp_path / "config.json"

        new_config = {"updated": True, "value": 123}
        app.save_config(new_config)

        # Read back
        saved = json.loads(app.config_path.read_text())
        assert saved["updated"] is True
        assert saved["value"] == 123


class TestArtifacts:
    """Test artifact handling."""

    def test_artifact_discovery(self, tmp_path):
        """Test artifacts are discovered correctly."""
        watcher = StateWatcher()
        watcher.artifact_root = tmp_path / "artifacts"

        # Create artifacts
        for i in range(5):
            cycle_dir = watcher.artifact_root / f"cycle_{i:03d}"
            cycle_dir.mkdir(parents=True)
            (cycle_dir / f"diff_{i}.patch").write_text(f"diff {i}")
            (cycle_dir / f"findings_{i}.json").write_text("[]")

        snapshot = watcher.snapshot()

        # Should find all artifacts (limit 50)
        assert len(snapshot.artifacts) >= 10  # At least diff + findings for 5 cycles

    def test_diff_viewer(self, tmp_path):
        """Test diff viewer loads diffs correctly."""
        watcher = StateWatcher()
        watcher.artifact_root = tmp_path / "artifacts"
        cycle_dir = watcher.artifact_root / "cycle_001"
        cycle_dir.mkdir(parents=True)

        diff_content = """--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def test():
-    pass
+    return True
"""
        (cycle_dir / "diff.patch").write_text(diff_content)

        snapshot = watcher.snapshot()

        assert "test.py" in snapshot.output.diff_text
        assert "return True" in snapshot.output.diff_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
