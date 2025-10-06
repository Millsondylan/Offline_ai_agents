"""Keyboard input handling and key mapping."""

import curses
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class KeyType(Enum):
    """Types of keyboard input."""

    NUMBER = auto()
    ARROW = auto()
    SPECIAL = auto()
    FUNCTION = auto()
    CTRL = auto()
    CHAR = auto()
    UNKNOWN = auto()


@dataclass
class MappedKey:
    """A mapped keyboard input."""

    type: KeyType
    value: Optional[str] = None
    code: Optional[int] = None


class Key:
    """Standardized key constants."""

    # Numbers
    NUM_1 = MappedKey(KeyType.NUMBER, "1", ord('1'))
    NUM_2 = MappedKey(KeyType.NUMBER, "2", ord('2'))
    NUM_3 = MappedKey(KeyType.NUMBER, "3", ord('3'))
    NUM_4 = MappedKey(KeyType.NUMBER, "4", ord('4'))
    NUM_5 = MappedKey(KeyType.NUMBER, "5", ord('5'))
    NUM_6 = MappedKey(KeyType.NUMBER, "6", ord('6'))
    NUM_7 = MappedKey(KeyType.NUMBER, "7", ord('7'))
    NUM_8 = MappedKey(KeyType.NUMBER, "8", ord('8'))
    NUM_9 = MappedKey(KeyType.NUMBER, "9", ord('9'))

    # Arrows
    UP = MappedKey(KeyType.ARROW, "up", curses.KEY_UP)
    DOWN = MappedKey(KeyType.ARROW, "down", curses.KEY_DOWN)
    LEFT = MappedKey(KeyType.ARROW, "left", curses.KEY_LEFT)
    RIGHT = MappedKey(KeyType.ARROW, "right", curses.KEY_RIGHT)

    # Special
    ENTER = MappedKey(KeyType.SPECIAL, "enter", 10)
    ESC = MappedKey(KeyType.SPECIAL, "esc", 27)
    BACKSPACE = MappedKey(KeyType.SPECIAL, "backspace", curses.KEY_BACKSPACE)
    DELETE = MappedKey(KeyType.SPECIAL, "delete", curses.KEY_DC)
    TAB = MappedKey(KeyType.SPECIAL, "tab", 9)

    # Page navigation
    PAGE_UP = MappedKey(KeyType.SPECIAL, "pageup", curses.KEY_PPAGE)
    PAGE_DOWN = MappedKey(KeyType.SPECIAL, "pagedown", curses.KEY_NPAGE)
    HOME = MappedKey(KeyType.SPECIAL, "home", curses.KEY_HOME)
    END = MappedKey(KeyType.SPECIAL, "end", curses.KEY_END)

    # Function keys
    F1 = MappedKey(KeyType.FUNCTION, "f1", curses.KEY_F1)
    F2 = MappedKey(KeyType.FUNCTION, "f2", curses.KEY_F2)
    F3 = MappedKey(KeyType.FUNCTION, "f3", curses.KEY_F3)
    F4 = MappedKey(KeyType.FUNCTION, "f4", curses.KEY_F4)
    F5 = MappedKey(KeyType.FUNCTION, "f5", curses.KEY_F5)
    F6 = MappedKey(KeyType.FUNCTION, "f6", curses.KEY_F6)
    F7 = MappedKey(KeyType.FUNCTION, "f7", curses.KEY_F7)
    F8 = MappedKey(KeyType.FUNCTION, "f8", curses.KEY_F8)
    F9 = MappedKey(KeyType.FUNCTION, "f9", curses.KEY_F9)
    F10 = MappedKey(KeyType.FUNCTION, "f10", curses.KEY_F10)
    F11 = MappedKey(KeyType.FUNCTION, "f11", curses.KEY_F11)
    F12 = MappedKey(KeyType.FUNCTION, "f12", curses.KEY_F12)

    # Ctrl combinations
    CTRL_A = MappedKey(KeyType.CTRL, "ctrl+a", 1)
    CTRL_C = MappedKey(KeyType.CTRL, "ctrl+c", 3)
    CTRL_Q = MappedKey(KeyType.CTRL, "ctrl+q", 17)
    CTRL_R = MappedKey(KeyType.CTRL, "ctrl+r", 18)
    CTRL_S = MappedKey(KeyType.CTRL, "ctrl+s", 19)
    CTRL_X = MappedKey(KeyType.CTRL, "ctrl+x", 24)

    # Sentinel
    UNKNOWN = MappedKey(KeyType.UNKNOWN)
    CHAR = KeyType.CHAR  # Used for printable characters


class KeyHandler:
    """Handles keyboard input mapping and sequences."""

    def __init__(self, sequence_timeout_ms: int = 100):
        """Initialize key handler.

        Args:
            sequence_timeout_ms: Timeout for escape sequences in milliseconds
        """
        self.sequence_timeout_ms = sequence_timeout_ms
        self._sequence: list[int] = []
        self._sequence_start: Optional[float] = None

        # Build reverse lookup maps
        self._key_map: dict[int, MappedKey] = {}
        for attr_name in dir(Key):
            attr = getattr(Key, attr_name)
            if isinstance(attr, MappedKey) and attr.code is not None:
                self._key_map[attr.code] = attr

    def map_key(self, key_code: int) -> MappedKey:
        """Map a key code to a standardized key.

        Args:
            key_code: Raw key code from curses

        Returns:
            Mapped key object
        """
        # Handle invalid keys
        if key_code < 0 or key_code > 1000000:
            return Key.UNKNOWN

        # Check direct mapping
        if key_code in self._key_map:
            return self._key_map[key_code]

        # Handle alternate representations
        if key_code == 13:  # \r
            return Key.ENTER
        if key_code == 127:  # DEL (backspace on some terminals)
            return Key.BACKSPACE

        # Handle printable characters
        if 32 <= key_code <= 126:
            return MappedKey(KeyType.CHAR, chr(key_code), key_code)

        return Key.UNKNOWN

    def start_sequence(self, key_code: int) -> None:
        """Start an escape sequence.

        Args:
            key_code: First key in sequence (usually ESC)
        """
        self._sequence = [key_code]
        self._sequence_start = time.time()

    def add_to_sequence(self, key_code: int) -> None:
        """Add a key to the current sequence.

        Args:
            key_code: Next key in sequence
        """
        self._sequence.append(key_code)

    def finish_sequence(self) -> MappedKey:
        """Complete and interpret the current sequence.

        Returns:
            Mapped key for the sequence, or ESC if timeout/invalid
        """
        if not self._sequence:
            return Key.UNKNOWN

        # Check timeout
        if self._sequence_start:
            elapsed_ms = (time.time() - self._sequence_start) * 1000
            if elapsed_ms > self.sequence_timeout_ms:
                self._sequence = []
                self._sequence_start = None
                return Key.ESC

        # Try to interpret sequence
        # Common sequences: ESC [ A = Up, ESC [ B = Down, etc.
        if len(self._sequence) == 3 and self._sequence[0] == 27 and self._sequence[1] == ord('['):
            third = self._sequence[2]
            if third == ord('A'):
                result = Key.UP
            elif third == ord('B'):
                result = Key.DOWN
            elif third == ord('C'):
                result = Key.RIGHT
            elif third == ord('D'):
                result = Key.LEFT
            else:
                result = Key.ESC
        else:
            result = Key.ESC

        self._sequence = []
        self._sequence_start = None
        return result
