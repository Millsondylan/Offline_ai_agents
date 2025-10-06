"""Screen layout calculations and window management."""

from dataclasses import dataclass
from typing import Tuple


class LayoutError(Exception):
    """Raised when layout cannot be created."""
    pass


@dataclass
class Area:
    """Represents a rectangular area on the screen."""
    y: int
    x: int
    height: int
    width: int


class LayoutManager:
    """Manages screen layout and window positioning."""

    MIN_HEIGHT = 24
    MIN_WIDTH = 80

    def __init__(self, total_height: int, total_width: int):
        """Initialize layout manager.

        Args:
            total_height: Total terminal height
            total_width: Total terminal width

        Raises:
            LayoutError: If terminal is too small
        """
        if total_height < self.MIN_HEIGHT or total_width < self.MIN_WIDTH:
            raise LayoutError(
                f"Terminal too small (min {self.MIN_WIDTH}x{self.MIN_HEIGHT})"
            )

        self.total_height = total_height
        self.total_width = total_width

        # Calculate dimensions
        self.header_height = 3
        self.footer_height = 2
        self.sidebar_width = self._calculate_sidebar_width()

    def _calculate_sidebar_width(self) -> int:
        """Calculate sidebar width based on terminal size."""
        if self.total_width >= 150:
            return 30
        elif self.total_width >= 100:
            return 25
        else:
            return 20

    def resize(self, new_height: int, new_width: int) -> None:
        """Update layout for new terminal size.

        Args:
            new_height: New terminal height
            new_width: New terminal width

        Raises:
            LayoutError: If new size is too small
        """
        if new_height < self.MIN_HEIGHT or new_width < self.MIN_WIDTH:
            raise LayoutError("Terminal too small after resize")

        self.total_height = new_height
        self.total_width = new_width
        self.sidebar_width = self._calculate_sidebar_width()

    def get_content_area(self) -> Area:
        """Get the main content area (excluding header, footer, sidebar).

        Returns:
            Area for main content
        """
        return Area(
            y=self.header_height,
            x=0,
            height=self.total_height - self.header_height - self.footer_height,
            width=self.total_width - self.sidebar_width,
        )

    def get_menu_area(self) -> Area:
        """Get the menu area (left portion of content).

        Returns:
            Area for menu display
        """
        content = self.get_content_area()
        return Area(
            y=content.y,
            x=0,
            height=content.height,
            width=min(40, content.width // 2),
        )

    def get_sidebar_area(self) -> Area:
        """Get the status sidebar area.

        Returns:
            Area for status sidebar
        """
        return Area(
            y=self.header_height,
            x=self.total_width - self.sidebar_width,
            height=self.total_height - self.header_height - self.footer_height,
            width=self.sidebar_width,
        )

    def get_breadcrumb_area(self) -> Area:
        """Get the breadcrumb area in footer.

        Returns:
            Area for breadcrumbs
        """
        return Area(
            y=self.total_height - 2,
            x=0,
            height=1,
            width=self.total_width,
        )

    def get_key_hints_area(self) -> Area:
        """Get the key hints area in footer.

        Returns:
            Area for key hints
        """
        return Area(
            y=self.total_height - 1,
            x=0,
            height=1,
            width=self.total_width,
        )

    def split_horizontal(self, ratio: float = 0.5) -> Tuple[Area, Area]:
        """Split content area horizontally.

        Args:
            ratio: Proportion for left panel (0.0 to 1.0)

        Returns:
            Tuple of (left_area, right_area)
        """
        content = self.get_content_area()
        split_x = int(content.width * ratio)

        left = Area(
            y=content.y,
            x=content.x,
            height=content.height,
            width=split_x,
        )

        right = Area(
            y=content.y,
            x=content.x + split_x,
            height=content.height,
            width=content.width - split_x,
        )

        return left, right

    def split_vertical(self, ratio: float = 0.5) -> Tuple[Area, Area]:
        """Split content area vertically.

        Args:
            ratio: Proportion for top panel (0.0 to 1.0)

        Returns:
            Tuple of (top_area, bottom_area)
        """
        content = self.get_content_area()
        split_y = int(content.height * ratio)

        top = Area(
            y=content.y,
            x=content.x,
            height=split_y,
            width=content.width,
        )

        bottom = Area(
            y=content.y + split_y,
            x=content.x,
            height=content.height - split_y,
            width=content.width,
        )

        return top, bottom
