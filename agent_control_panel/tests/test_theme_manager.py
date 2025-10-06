"""Tests for ThemeManager - Phase 1: Core UI Framework."""

import curses
from unittest.mock import Mock, patch

import pytest


class TestThemeManager:
    """Test theme management and color schemes."""

    def test_dark_theme_initialization(self):
        """Test dark theme initializes with correct colors."""
        from agent_control_panel.core.theme_manager import ThemeManager, Theme

        manager = ThemeManager()
        assert manager.current_theme == Theme.DARK
        assert manager.colors is not None
        assert "header_bg" in manager.colors
        assert "error_fg" in manager.colors

    def test_light_theme_initialization(self):
        """Test light theme initializes with correct colors."""
        from agent_control_panel.core.theme_manager import ThemeManager, Theme

        manager = ThemeManager(initial_theme=Theme.LIGHT)
        assert manager.current_theme == Theme.LIGHT
        assert manager.colors["bg"] != manager._dark_colors["bg"]

    def test_theme_toggle_switches_correctly(self):
        """Test toggling between dark and light themes."""
        from agent_control_panel.core.theme_manager import ThemeManager, Theme

        manager = ThemeManager()
        assert manager.current_theme == Theme.DARK

        manager.toggle_theme()
        assert manager.current_theme == Theme.LIGHT

        manager.toggle_theme()
        assert manager.current_theme == Theme.DARK

    def test_monochrome_fallback_when_no_colors(self):
        """Test graceful fallback to monochrome when colors unavailable."""
        from agent_control_panel.core.theme_manager import ThemeManager

        with patch("curses.has_colors", return_value=False):
            manager = ThemeManager()
            assert manager.use_colors is False
            # Should still have color definitions but won't use them
            assert manager.colors is not None

    def test_color_pair_registration(self, mock_stdscr):
        """Test curses color pairs are registered correctly."""
        from agent_control_panel.core.theme_manager import ThemeManager

        with patch("curses.init_pair") as mock_init:
            manager = ThemeManager()
            manager.initialize_colors()
            # Should register multiple color pairs
            assert mock_init.call_count >= 8  # At least 8 color pairs

    def test_theme_persistence_across_restarts(self, tmp_path):
        """Test theme preference is saved and restored."""
        from agent_control_panel.core.theme_manager import ThemeManager, Theme

        config_file = tmp_path / "theme.json"

        # Create manager, toggle to light, save
        manager1 = ThemeManager(config_path=config_file)
        manager1.toggle_theme()
        manager1.save_preference()

        # Create new manager, should load light theme
        manager2 = ThemeManager(config_path=config_file)
        assert manager2.current_theme == Theme.LIGHT

    def test_get_color_pair_returns_valid_id(self):
        """Test getting color pair ID for a named style."""
        from agent_control_panel.core.theme_manager import ThemeManager

        manager = ThemeManager()
        manager.initialize_colors()

        pair_id = manager.get_color_pair("header")
        assert isinstance(pair_id, int)
        assert pair_id > 0

    def test_invalid_color_name_raises_error(self):
        """Test requesting invalid color name raises appropriate error."""
        from agent_control_panel.core.theme_manager import ThemeManager

        manager = ThemeManager()
        manager.initialize_colors()

        with pytest.raises(KeyError):
            manager.get_color_pair("nonexistent_color")

    def test_theme_colors_have_required_keys(self):
        """Test both themes have all required color definitions."""
        from agent_control_panel.core.theme_manager import ThemeManager

        required_keys = [
            "bg", "fg", "header_bg", "header_fg",
            "status_bg", "status_fg", "menu_bg", "menu_fg",
            "error_fg", "warn_fg", "info_fg", "success_fg",
            "border", "highlight", "selected_bg", "selected_fg"
        ]

        manager = ThemeManager()

        for key in required_keys:
            assert key in manager._dark_colors, f"Dark theme missing {key}"
            assert key in manager._light_colors, f"Light theme missing {key}"
