"""Theme management and color schemes."""

import curses
import json
from enum import Enum
from pathlib import Path
from typing import Dict, Optional


class Theme(str, Enum):
    """Available themes."""
    DARK = "dark"
    LIGHT = "light"


class ThemeManager:
    """Manages UI themes and color schemes."""

    def __init__(
        self,
        initial_theme: Theme = Theme.DARK,
        config_path: Optional[Path] = None,
    ):
        """Initialize theme manager.

        Args:
            initial_theme: Theme to use initially
            config_path: Path to save theme preference
        """
        self.current_theme = initial_theme
        self.config_path = config_path or Path.home() / ".agent_cli" / "theme.json"
        self.use_colors = True  # Will be set in initialize_colors

        # Define color schemes
        self._dark_colors = {
            "bg": curses.COLOR_BLACK,
            "fg": curses.COLOR_WHITE,
            "header_bg": curses.COLOR_BLUE,
            "header_fg": curses.COLOR_WHITE,
            "status_bg": curses.COLOR_BLACK,
            "status_fg": curses.COLOR_CYAN,
            "menu_bg": curses.COLOR_BLACK,
            "menu_fg": curses.COLOR_WHITE,
            "error_fg": curses.COLOR_RED,
            "warn_fg": curses.COLOR_YELLOW,
            "info_fg": curses.COLOR_WHITE,
            "success_fg": curses.COLOR_GREEN,
            "border": curses.COLOR_BLUE,
            "highlight": curses.COLOR_CYAN,
            "selected_bg": curses.COLOR_BLUE,
            "selected_fg": curses.COLOR_WHITE,
        }

        self._light_colors = {
            "bg": curses.COLOR_WHITE,
            "fg": curses.COLOR_BLACK,
            "header_bg": curses.COLOR_CYAN,
            "header_fg": curses.COLOR_BLACK,
            "status_bg": curses.COLOR_WHITE,
            "status_fg": curses.COLOR_BLUE,
            "menu_bg": curses.COLOR_WHITE,
            "menu_fg": curses.COLOR_BLACK,
            "error_fg": curses.COLOR_RED,
            "warn_fg": curses.COLOR_YELLOW,
            "info_fg": curses.COLOR_BLACK,
            "success_fg": curses.COLOR_GREEN,
            "border": curses.COLOR_BLUE,
            "highlight": curses.COLOR_MAGENTA,
            "selected_bg": curses.COLOR_CYAN,
            "selected_fg": curses.COLOR_BLACK,
        }

        self.colors = self._dark_colors if self.current_theme == Theme.DARK else self._light_colors
        self._color_pairs: Dict[str, int] = {}

        # Load saved preference
        self._load_preference()

    def _load_preference(self) -> None:
        """Load theme preference from disk."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                    theme_str = data.get("theme", "dark")
                    self.current_theme = Theme(theme_str)
                    self.colors = (
                        self._dark_colors
                        if self.current_theme == Theme.DARK
                        else self._light_colors
                    )
            except (json.JSONDecodeError, ValueError, KeyError):
                pass  # Use default

    def save_preference(self) -> None:
        """Save theme preference to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump({"theme": self.current_theme.value}, f)

    def toggle_theme(self) -> None:
        """Toggle between dark and light themes."""
        if self.current_theme == Theme.DARK:
            self.current_theme = Theme.LIGHT
            self.colors = self._light_colors
        else:
            self.current_theme = Theme.DARK
            self.colors = self._dark_colors

        # Re-initialize color pairs if already initialized
        if self._color_pairs:
            self.initialize_colors()

    def initialize_colors(self) -> None:
        """Initialize curses color pairs."""
        self.use_colors = curses.has_colors()

        if not self.use_colors:
            return

        curses.start_color()
        curses.use_default_colors()

        # Register color pairs
        pair_id = 1

        # Header
        curses.init_pair(pair_id, self.colors["header_fg"], self.colors["header_bg"])
        self._color_pairs["header"] = pair_id
        pair_id += 1

        # Status sidebar
        curses.init_pair(pair_id, self.colors["status_fg"], self.colors["status_bg"])
        self._color_pairs["status"] = pair_id
        pair_id += 1

        # Menu
        curses.init_pair(pair_id, self.colors["menu_fg"], self.colors["menu_bg"])
        self._color_pairs["menu"] = pair_id
        pair_id += 1

        # Error text
        curses.init_pair(pair_id, self.colors["error_fg"], self.colors["bg"])
        self._color_pairs["error"] = pair_id
        pair_id += 1

        # Warning text
        curses.init_pair(pair_id, self.colors["warn_fg"], self.colors["bg"])
        self._color_pairs["warning"] = pair_id
        pair_id += 1

        # Info text
        curses.init_pair(pair_id, self.colors["info_fg"], self.colors["bg"])
        self._color_pairs["info"] = pair_id
        pair_id += 1

        # Success text
        curses.init_pair(pair_id, self.colors["success_fg"], self.colors["bg"])
        self._color_pairs["success"] = pair_id
        pair_id += 1

        # Border
        curses.init_pair(pair_id, self.colors["border"], self.colors["bg"])
        self._color_pairs["border"] = pair_id
        pair_id += 1

        # Highlight
        curses.init_pair(pair_id, self.colors["highlight"], self.colors["bg"])
        self._color_pairs["highlight"] = pair_id
        pair_id += 1

        # Selected item
        curses.init_pair(pair_id, self.colors["selected_fg"], self.colors["selected_bg"])
        self._color_pairs["selected"] = pair_id
        pair_id += 1

        # Normal text
        curses.init_pair(pair_id, self.colors["fg"], self.colors["bg"])
        self._color_pairs["normal"] = pair_id

    def get_color_pair(self, name: str) -> int:
        """Get color pair ID for a named style.

        Args:
            name: Color scheme name

        Returns:
            curses color pair ID

        Raises:
            KeyError: If color name doesn't exist
        """
        if name not in self._color_pairs:
            raise KeyError(f"Color pair '{name}' not found")
        return curses.color_pair(self._color_pairs[name])

    def get_color_attr(self, name: str, bold: bool = False) -> int:
        """Get color attribute with optional bold.

        Args:
            name: Color scheme name
            bold: Whether to make text bold

        Returns:
            curses attribute value
        """
        if not self.use_colors:
            return curses.A_BOLD if bold else curses.A_NORMAL

        attr = self.get_color_pair(name)
        if bold:
            attr |= curses.A_BOLD
        return attr
