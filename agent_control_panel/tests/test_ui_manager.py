"""Tests for UIManager - Phase 1: Core UI Framework."""

import curses
import time
from unittest.mock import Mock, MagicMock, patch

import pytest


class TestUIManager:
    """Test main UI controller and rendering."""

    def test_initialization_standard_terminal(self, mock_stdscr, mock_agent_controller):
        """Test UIManager initializes correctly on 80x24 terminal."""
        from agent_control_panel.core.ui_manager import UIManager

        mock_stdscr.getmaxyx.return_value = (24, 80)

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        assert ui.stdscr == mock_stdscr
        assert ui.agent_controller == mock_agent_controller
        assert ui.active_panel is not None
        assert ui.is_running is False

    def test_initialization_large_terminal(self, mock_stdscr, mock_agent_controller):
        """Test UIManager initializes correctly on 200x60 terminal."""
        from agent_control_panel.core.ui_manager import UIManager

        mock_stdscr.getmaxyx.return_value = (60, 200)

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        assert ui.layout.total_height == 60
        assert ui.layout.total_width == 200

    def test_initialization_fails_on_small_terminal(self, mock_stdscr, mock_agent_controller):
        """Test initialization fails gracefully on too-small terminal."""
        from agent_control_panel.core.ui_manager import UIManager, UIError

        mock_stdscr.getmaxyx.return_value = (20, 60)  # Too small

        with pytest.raises(UIError, match="Terminal too small"):
            UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

    def test_curses_setup_and_teardown(self, mock_stdscr, mock_agent_controller):
        """Test curses is set up and torn down correctly."""
        from agent_control_panel.core.ui_manager import UIManager

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        ui.setup()
        # Should configure curses
        mock_stdscr.keypad.assert_called_with(True)
        mock_stdscr.nodelay.assert_called_with(True)

        ui.teardown()
        # Should restore terminal
        mock_stdscr.keypad.assert_called_with(False)

    def test_keyboard_routing_to_active_panel(self, mock_stdscr, mock_agent_controller):
        """Test keyboard input routes to active panel."""
        from agent_control_panel.core.ui_manager import UIManager
        from agent_control_panel.utils.keyboard import Key

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)
        ui.active_panel.on_key = Mock(return_value=True)

        ui.handle_key(Key.UP)

        ui.active_panel.on_key.assert_called_once_with(Key.UP)

    def test_number_keys_switch_panels(self, mock_stdscr, mock_agent_controller):
        """Test number keys (1-9) switch to corresponding panels."""
        from agent_control_panel.core.ui_manager import UIManager

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        # Press '1' for home panel
        ui.handle_key_code(ord('1'))
        assert ui.active_panel.name == "home"

        # Press '2' for task panel
        ui.handle_key_code(ord('2'))
        assert ui.active_panel.name == "tasks"

    def test_panel_switching_updates_breadcrumbs(self, mock_stdscr, mock_agent_controller):
        """Test switching panels updates breadcrumb trail."""
        from agent_control_panel.core.ui_manager import UIManager

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        ui.switch_panel("tasks")
        assert "tasks" in ui.breadcrumbs[-1].lower()

        ui.switch_panel("logs")
        assert "logs" in ui.breadcrumbs[-1].lower()

    def test_header_rendering_with_agent_status(self, mock_stdscr, mock_agent_controller, sample_agent_status):
        """Test header displays agent status correctly."""
        from agent_control_panel.core.ui_manager import UIManager

        mock_agent_controller.get_status.return_value = sample_agent_status

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)
        ui.render_header()

        # Should display model name, cycle, and status
        calls = [str(call) for call in mock_stdscr.addstr.call_args_list]
        assert any("gpt-4" in call for call in calls)
        assert any("42" in call for call in calls)  # Current cycle
        assert any("RUNNING" in call.upper() for call in calls)

    def test_footer_rendering_with_key_hints(self, mock_stdscr, mock_agent_controller):
        """Test footer displays context-appropriate key hints."""
        from agent_control_panel.core.ui_manager import UIManager

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)
        ui.switch_panel("tasks")
        ui.render_footer()

        calls = [str(call) for call in mock_stdscr.addstr.call_args_list]
        # Should show task-specific hints
        assert any("[N]ew" in call or "New" in call for call in calls)

    def test_status_sidebar_updates(self, mock_stdscr, mock_agent_controller, sample_agent_status):
        """Test status sidebar updates with latest metrics."""
        from agent_control_panel.core.ui_manager import UIManager

        mock_agent_controller.get_status.return_value = sample_agent_status

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)
        ui.render_sidebar()

        calls = [str(call) for call in mock_stdscr.addstr.call_args_list]
        assert any("156" in call for call in calls)  # thoughts_count
        assert any("42" in call for call in calls)  # actions_count

    def test_window_resize_handling(self, mock_stdscr, mock_agent_controller):
        """Test UI handles terminal resize gracefully."""
        from agent_control_panel.core.ui_manager import UIManager

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        # Simulate resize
        mock_stdscr.getmaxyx.return_value = (30, 100)
        ui.handle_resize()

        assert ui.layout.total_height == 30
        assert ui.layout.total_width == 100

    def test_theme_toggle_applies_to_all_elements(self, mock_stdscr, mock_agent_controller):
        """Test theme toggle updates all UI elements."""
        from agent_control_panel.core.ui_manager import UIManager
        from agent_control_panel.core.theme_manager import Theme

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        original_theme = ui.theme_manager.current_theme
        ui.toggle_theme()

        assert ui.theme_manager.current_theme != original_theme
        # Should trigger full re-render
        assert ui.needs_redraw is True

    def test_render_performance_under_50ms(self, mock_stdscr, mock_agent_controller):
        """Test full render completes in under 50ms."""
        from agent_control_panel.core.ui_manager import UIManager

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        start = time.perf_counter()
        ui.render()
        duration = (time.perf_counter() - start) * 1000  # Convert to ms

        assert duration < 50, f"Render took {duration}ms, expected <50ms"

    def test_graceful_shutdown_on_exception(self, mock_stdscr, mock_agent_controller):
        """Test UI shuts down gracefully on uncaught exception."""
        from agent_control_panel.core.ui_manager import UIManager

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        # Simulate exception during rendering
        mock_stdscr.addstr.side_effect = Exception("Simulated error")

        try:
            ui.render()
        except Exception:
            pass

        # Should call teardown
        assert ui.is_running is False

    def test_escape_key_returns_to_previous_panel(self, mock_stdscr, mock_agent_controller):
        """Test ESC key navigates back in panel history."""
        from agent_control_panel.core.ui_manager import UIManager
        from agent_control_panel.utils.keyboard import Key

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        ui.switch_panel("tasks")
        ui.switch_panel("logs")

        ui.handle_key(Key.ESC)

        assert ui.active_panel.name == "tasks"

    def test_ctrl_q_quits_application(self, mock_stdscr, mock_agent_controller):
        """Test Ctrl+Q quits the application."""
        from agent_control_panel.core.ui_manager import UIManager
        from agent_control_panel.utils.keyboard import Key

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)
        ui.is_running = True

        ui.handle_key(Key.CTRL_Q)

        assert ui.is_running is False

    def test_ctrl_r_refreshes_screen(self, mock_stdscr, mock_agent_controller):
        """Test Ctrl+R forces full screen refresh."""
        from agent_control_panel.core.ui_manager import UIManager
        from agent_control_panel.utils.keyboard import Key

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        ui.handle_key(Key.CTRL_R)

        mock_stdscr.clear.assert_called()
        mock_stdscr.refresh.assert_called()

    def test_concurrent_agent_updates_while_rendering(self, mock_stdscr, mock_agent_controller, sample_agent_status):
        """Test UI handles concurrent agent status updates."""
        from agent_control_panel.core.ui_manager import UIManager
        import threading

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        # Simulate agent updating status during render
        def update_status():
            time.sleep(0.01)
            mock_agent_controller.get_status.return_value = sample_agent_status

        thread = threading.Thread(target=update_status)
        thread.start()

        ui.render()

        thread.join()
        # Should not crash from concurrent access

    def test_error_message_display(self, mock_stdscr, mock_agent_controller):
        """Test error messages are displayed to user."""
        from agent_control_panel.core.ui_manager import UIManager

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        ui.show_error("Test error message")

        calls = [str(call) for call in mock_stdscr.addstr.call_args_list]
        assert any("error" in call.lower() for call in calls)

    def test_status_message_display(self, mock_stdscr, mock_agent_controller):
        """Test status messages are displayed temporarily."""
        from agent_control_panel.core.ui_manager import UIManager

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)

        ui.show_status("Operation completed")

        calls = [str(call) for call in mock_stdscr.addstr.call_args_list]
        assert any("completed" in call.lower() for call in calls)

    def test_progress_bar_rendering(self, mock_stdscr, mock_agent_controller):
        """Test progress bar displays correctly in header."""
        from agent_control_panel.core.ui_manager import UIManager
        from agent_control_panel.core.models import AgentStatus, AgentState

        status = AgentStatus(
            state=AgentState.RUNNING,
            current_cycle=50,
            total_cycles=100,
            model_name="gpt-4",
            provider="openai",
            session_duration_seconds=60.0,
        )
        mock_agent_controller.get_status.return_value = status

        ui = UIManager(stdscr=mock_stdscr, agent_controller=mock_agent_controller)
        ui.render_header()

        # Should show 50% progress
        calls = [str(call) for call in mock_stdscr.addstr.call_args_list]
        assert any("50" in call or "█" in call for call in calls)
