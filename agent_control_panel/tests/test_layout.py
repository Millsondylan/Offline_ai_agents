"""Tests for screen layout calculations - Phase 1: Core UI Framework."""

import pytest


class TestLayout:
    """Test screen layout and window calculations."""

    def test_header_height_calculation(self):
        """Test header height is calculated correctly."""
        from agent_control_panel.utils.layout import LayoutManager

        layout = LayoutManager(total_height=24, total_width=80)
        assert layout.header_height == 3  # Status line + model info + separator

    def test_content_area_calculation_standard_terminal(self):
        """Test content area calculated for 80x24 terminal."""
        from agent_control_panel.utils.layout import LayoutManager

        layout = LayoutManager(total_height=24, total_width=80)

        content = layout.get_content_area()
        assert content.y == 3  # After header
        assert content.x == 0
        assert content.height == 24 - 3 - 2  # Minus header and footer
        assert content.width == 80 - 20  # Minus sidebar

    def test_content_area_calculation_large_terminal(self):
        """Test content area calculated for 200x60 terminal."""
        from agent_control_panel.utils.layout import LayoutManager

        layout = LayoutManager(total_height=60, total_width=200)

        content = layout.get_content_area()
        assert content.height == 60 - 3 - 2  # Minus header and footer
        assert content.width == 200 - 30  # Wider sidebar on large screen

    def test_sidebar_width_calculation(self):
        """Test sidebar width scales with terminal size."""
        from agent_control_panel.utils.layout import LayoutManager

        # Small terminal: fixed sidebar
        layout_small = LayoutManager(total_height=24, total_width=80)
        assert layout_small.sidebar_width == 20

        # Large terminal: wider sidebar
        layout_large = LayoutManager(total_height=60, total_width=200)
        assert layout_large.sidebar_width == 30

    def test_footer_height_calculation(self):
        """Test footer height is correct."""
        from agent_control_panel.utils.layout import LayoutManager

        layout = LayoutManager(total_height=24, total_width=80)
        assert layout.footer_height == 2  # Breadcrumbs + key hints

    def test_window_splitting_for_multi_column(self):
        """Test splitting content area into multiple columns."""
        from agent_control_panel.utils.layout import LayoutManager

        layout = LayoutManager(total_height=24, total_width=80)

        left, right = layout.split_horizontal(ratio=0.5)
        assert left.width + right.width <= layout.get_content_area().width
        assert left.height == right.height

    def test_layout_adjusts_on_resize(self):
        """Test layout recalculates when terminal resized."""
        from agent_control_panel.utils.layout import LayoutManager

        layout = LayoutManager(total_height=24, total_width=80)
        original_content = layout.get_content_area()

        layout.resize(40, 120)
        new_content = layout.get_content_area()

        assert new_content.height != original_content.height
        assert new_content.width != original_content.width

    def test_minimum_terminal_size_validation(self):
        """Test layout rejects too-small terminals."""
        from agent_control_panel.utils.layout import LayoutManager, LayoutError

        # Should work
        LayoutManager(total_height=24, total_width=80)

        # Should raise error
        with pytest.raises(LayoutError):
            LayoutManager(total_height=10, total_width=40)

    def test_menu_area_calculation(self):
        """Test menu area positioned correctly."""
        from agent_control_panel.utils.layout import LayoutManager

        layout = LayoutManager(total_height=24, total_width=80)
        menu = layout.get_menu_area()

        assert menu.y == 3  # After header
        assert menu.width < layout.get_content_area().width  # Left side only

    def test_status_sidebar_area(self):
        """Test status sidebar area calculation."""
        from agent_control_panel.utils.layout import LayoutManager

        layout = LayoutManager(total_height=24, total_width=80)
        sidebar = layout.get_sidebar_area()

        assert sidebar.x == 80 - 20  # Right side
        assert sidebar.width == 20
        assert sidebar.height == 24 - 3 - 2  # Full height minus header/footer

    def test_breadcrumb_area(self):
        """Test breadcrumb area in footer."""
        from agent_control_panel.utils.layout import LayoutManager

        layout = LayoutManager(total_height=24, total_width=80)
        breadcrumb = layout.get_breadcrumb_area()

        assert breadcrumb.y == 24 - 2  # In footer
        assert breadcrumb.height == 1

    def test_key_hints_area(self):
        """Test key hints area in footer."""
        from agent_control_panel.utils.layout import LayoutManager

        layout = LayoutManager(total_height=24, total_width=80)
        hints = layout.get_key_hints_area()

        assert hints.y == 24 - 1  # Bottom line
        assert hints.height == 1

    def test_panel_rendering_bounds(self):
        """Test panels stay within their assigned bounds."""
        from agent_control_panel.utils.layout import LayoutManager

        layout = LayoutManager(total_height=24, total_width=80)
        content = layout.get_content_area()

        # Panel should never exceed content area
        assert content.y >= 0
        assert content.x >= 0
        assert content.y + content.height <= 24
        assert content.x + content.width <= 80
