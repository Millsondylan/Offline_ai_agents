"""Tests for keyboard input handling - Phase 1: Core UI Framework."""

import curses

import pytest


class TestKeyboard:
    """Test keyboard input mapping and handling."""

    def test_number_key_mapping(self):
        """Test number keys (1-9) map correctly."""
        from agent_control_panel.utils.keyboard import KeyHandler, Key

        handler = KeyHandler()

        assert handler.map_key(ord('1')) == Key.NUM_1
        assert handler.map_key(ord('5')) == Key.NUM_5
        assert handler.map_key(ord('9')) == Key.NUM_9

    def test_arrow_key_mapping(self):
        """Test arrow keys map correctly."""
        from agent_control_panel.utils.keyboard import KeyHandler, Key

        handler = KeyHandler()

        assert handler.map_key(curses.KEY_UP) == Key.UP
        assert handler.map_key(curses.KEY_DOWN) == Key.DOWN
        assert handler.map_key(curses.KEY_LEFT) == Key.LEFT
        assert handler.map_key(curses.KEY_RIGHT) == Key.RIGHT

    def test_special_key_mapping(self):
        """Test special keys (Enter, ESC, etc.) map correctly."""
        from agent_control_panel.utils.keyboard import KeyHandler, Key

        handler = KeyHandler()

        assert handler.map_key(10) == Key.ENTER  # \n
        assert handler.map_key(13) == Key.ENTER  # \r
        assert handler.map_key(27) == Key.ESC
        assert handler.map_key(curses.KEY_BACKSPACE) == Key.BACKSPACE
        assert handler.map_key(127) == Key.BACKSPACE  # DEL on some terminals

    def test_function_key_mapping(self):
        """Test function keys map correctly."""
        from agent_control_panel.utils.keyboard import KeyHandler, Key

        handler = KeyHandler()

        assert handler.map_key(curses.KEY_F1) == Key.F1
        assert handler.map_key(curses.KEY_F5) == Key.F5
        assert handler.map_key(curses.KEY_F12) == Key.F12

    def test_page_navigation_keys(self):
        """Test page up/down and home/end keys."""
        from agent_control_panel.utils.keyboard import KeyHandler, Key

        handler = KeyHandler()

        assert handler.map_key(curses.KEY_PPAGE) == Key.PAGE_UP
        assert handler.map_key(curses.KEY_NPAGE) == Key.PAGE_DOWN
        assert handler.map_key(curses.KEY_HOME) == Key.HOME
        assert handler.map_key(curses.KEY_END) == Key.END

    def test_ctrl_key_mapping(self):
        """Test Ctrl+ key combinations."""
        from agent_control_panel.utils.keyboard import KeyHandler, Key

        handler = KeyHandler()

        # Ctrl+S = 19
        assert handler.map_key(19) == Key.CTRL_S
        # Ctrl+Q = 17
        assert handler.map_key(17) == Key.CTRL_Q
        # Ctrl+C = 3
        assert handler.map_key(3) == Key.CTRL_C

    def test_printable_character_mapping(self):
        """Test printable characters map to CHAR with correct value."""
        from agent_control_panel.utils.keyboard import KeyHandler, Key

        handler = KeyHandler()

        result = handler.map_key(ord('a'))
        assert result.type == Key.CHAR
        assert result.value == 'a'

        result = handler.map_key(ord('Z'))
        assert result.type == Key.CHAR
        assert result.value == 'Z'

    def test_invalid_key_handling(self):
        """Test invalid key codes are handled gracefully."""
        from agent_control_panel.utils.keyboard import KeyHandler, Key

        handler = KeyHandler()

        # Negative key code
        result = handler.map_key(-1)
        assert result == Key.UNKNOWN

        # Very large key code
        result = handler.map_key(999999)
        assert result == Key.UNKNOWN

    def test_key_sequence_detection(self):
        """Test multi-key sequences (like ESC [ A for up arrow)."""
        from agent_control_panel.utils.keyboard import KeyHandler

        handler = KeyHandler()

        # Should handle escape sequences
        handler.start_sequence(27)  # ESC
        handler.add_to_sequence(ord('['))
        handler.add_to_sequence(ord('A'))

        result = handler.finish_sequence()
        from agent_control_panel.utils.keyboard import Key
        assert result == Key.UP

    def test_timeout_handling(self):
        """Test key input timeout for unfinished sequences."""
        from agent_control_panel.utils.keyboard import KeyHandler

        handler = KeyHandler(sequence_timeout_ms=100)

        handler.start_sequence(27)  # ESC
        # Don't complete the sequence

        # After timeout, should treat as standalone ESC
        import time
        time.sleep(0.15)

        result = handler.finish_sequence()
        from agent_control_panel.utils.keyboard import Key
        assert result == Key.ESC
