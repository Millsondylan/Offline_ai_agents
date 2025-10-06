"""Tests for BasePanel - Phase 1: Core UI Framework."""

import pytest
from unittest.mock import Mock, MagicMock


class TestBasePanel:
    """Test base panel functionality."""

    def test_panel_initialization(self, mock_stdscr):
        """Test panel initializes with correct default state."""
        from agent_control_panel.panels.base_panel import BasePanel

        panel = BasePanel(name="test", window=mock_stdscr)

        assert panel.name == "test"
        assert panel.is_active is False
        assert panel.scroll_offset == 0
        assert panel.window == mock_stdscr

    def test_panel_activation(self, mock_stdscr):
        """Test panel activation sets state correctly."""
        from agent_control_panel.panels.base_panel import BasePanel

        panel = BasePanel(name="test", window=mock_stdscr)
        panel.activate()

        assert panel.is_active is True

    def test_panel_deactivation(self, mock_stdscr):
        """Test panel deactivation sets state correctly."""
        from agent_control_panel.panels.base_panel import BasePanel

        panel = BasePanel(name="test", window=mock_stdscr)
        panel.activate()
        panel.deactivate()

        assert panel.is_active is False

    def test_panel_key_handling_delegation(self, mock_stdscr):
        """Test panel delegates key handling to handle_key method."""
        from agent_control_panel.panels.base_panel import BasePanel
        from agent_control_panel.utils.keyboard import Key

        panel = BasePanel(name="test", window=mock_stdscr)
        panel.handle_key = Mock(return_value=True)

        result = panel.on_key(Key.UP)

        panel.handle_key.assert_called_once_with(Key.UP)
        assert result is True

    def test_panel_scroll_state_persistence(self, mock_stdscr, mock_state_manager):
        """Test panel scroll position is saved and restored."""
        from agent_control_panel.panels.base_panel import BasePanel

        panel = BasePanel(name="test", window=mock_stdscr, state_manager=mock_state_manager)

        # Set scroll position
        panel.scroll_offset = 42
        panel.save_state()

        mock_state_manager.set.assert_called_with("test.scroll_offset", 42)

    def test_panel_render_boundaries(self, mock_stdscr):
        """Test panel rendering respects window boundaries."""
        from agent_control_panel.panels.base_panel import BasePanel

        mock_stdscr.getmaxyx.return_value = (10, 40)
        panel = BasePanel(name="test", window=mock_stdscr)

        panel.render()

        # Should not attempt to write outside bounds
        for call in mock_stdscr.addstr.call_args_list:
            y, x = call[0][0], call[0][1]
            assert 0 <= y < 10
            assert 0 <= x < 40

    def test_panel_focus_management(self, mock_stdscr):
        """Test panel tracks focus state."""
        from agent_control_panel.panels.base_panel import BasePanel

        panel = BasePanel(name="test", window=mock_stdscr)

        assert panel.has_focus() is False

        panel.activate()
        assert panel.has_focus() is True

        panel.deactivate()
        assert panel.has_focus() is False

    def test_panel_clear_on_render(self, mock_stdscr):
        """Test panel clears its window before rendering."""
        from agent_control_panel.panels.base_panel import BasePanel

        panel = BasePanel(name="test", window=mock_stdscr)
        panel.render()

        mock_stdscr.clear.assert_called()

    def test_panel_title_rendering(self, mock_stdscr):
        """Test panel renders title bar."""
        from agent_control_panel.panels.base_panel import BasePanel

        panel = BasePanel(name="Test Panel", window=mock_stdscr)
        panel.render()

        # Should have written title
        calls = [str(call) for call in mock_stdscr.addstr.call_args_list]
        assert any("Test Panel" in call for call in calls)

    def test_panel_scroll_up(self, mock_stdscr):
        """Test scrolling up decreases offset."""
        from agent_control_panel.panels.base_panel import BasePanel

        panel = BasePanel(name="test", window=mock_stdscr)
        panel.scroll_offset = 10

        panel.scroll_up(3)
        assert panel.scroll_offset == 7

    def test_panel_scroll_down(self, mock_stdscr):
        """Test scrolling down increases offset."""
        from agent_control_panel.panels.base_panel import BasePanel

        panel = BasePanel(name="test", window=mock_stdscr)
        panel.scroll_offset = 10

        panel.scroll_down(5)
        assert panel.scroll_offset == 15

    def test_panel_scroll_bounds_checking(self, mock_stdscr):
        """Test scrolling respects content bounds."""
        from agent_control_panel.panels.base_panel import BasePanel

        panel = BasePanel(name="test", window=mock_stdscr)
        panel.max_scroll = 100

        # Can't scroll below 0
        panel.scroll_offset = 5
        panel.scroll_up(10)
        assert panel.scroll_offset == 0

        # Can't scroll above max
        panel.scroll_offset = 95
        panel.scroll_down(10)
        assert panel.scroll_offset == 100

    def test_panel_refresh_after_render(self, mock_stdscr):
        """Test panel calls refresh after rendering."""
        from agent_control_panel.panels.base_panel import BasePanel

        panel = BasePanel(name="test", window=mock_stdscr)
        panel.render()

        mock_stdscr.refresh.assert_called()

    def test_panel_error_handling_in_render(self, mock_stdscr):
        """Test panel handles rendering errors gracefully."""
        from agent_control_panel.panels.base_panel import BasePanel

        mock_stdscr.addstr.side_effect = Exception("Rendering error")
        panel = BasePanel(name="test", window=mock_stdscr)

        # Should not crash
        panel.render()
        assert True  # If we got here, error was handled
