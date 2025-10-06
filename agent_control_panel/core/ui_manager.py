"""Main UI controller and rendering manager."""

import curses
import logging
import time
from typing import Any, Dict, List, Optional

from agent_control_panel.core.models import AgentStatus
from agent_control_panel.core.theme_manager import ThemeManager
from agent_control_panel.panels.base_panel import BasePanel
from agent_control_panel.utils.keyboard import Key, KeyHandler, MappedKey
from agent_control_panel.utils.layout import LayoutManager, LayoutError


logger = logging.getLogger(__name__)


class UIError(Exception):
    """Raised when UI cannot be initialized or operated."""
    pass


class UIManager:
    """Main UI controller managing panels, input, and rendering."""

    def __init__(
        self,
        stdscr: Any,
        agent_controller: Any,
        state_manager: Optional[Any] = None,
    ):
        """Initialize UI manager.

        Args:
            stdscr: curses standard screen
            agent_controller: Agent controller for communication
            state_manager: Optional state manager for persistence

        Raises:
            UIError: If terminal is too small or initialization fails
        """
        self.stdscr = stdscr
        self.agent_controller = agent_controller
        self.state_manager = state_manager

        # Get terminal size
        height, width = self.stdscr.getmaxyx()

        # Initialize layout manager
        try:
            self.layout = LayoutManager(height, width)
        except LayoutError as e:
            raise UIError(str(e)) from e

        # Initialize theme manager
        self.theme_manager = ThemeManager()

        # Initialize keyboard handler
        self.key_handler = KeyHandler()

        # Panel management
        self.panels: Dict[str, BasePanel] = {}
        self.active_panel: Optional[BasePanel] = None
        self.panel_history: List[str] = []

        # UI state
        self.is_running = False
        self.needs_redraw = True
        self.status_message: Optional[str] = None
        self.status_message_time: float = 0
        self.error_message: Optional[str] = None

        # Breadcrumbs
        self.breadcrumbs: List[str] = ["Home"]

        # Create windows (will be done in setup)
        self._windows_created = False

    def setup(self) -> None:
        """Set up curses and initialize UI."""
        try:
            # Configure curses
            self.stdscr.keypad(True)
            self.stdscr.nodelay(True)  # Non-blocking input
            curses.curs_set(0)  # Hide cursor
            curses.noecho()
            curses.cbreak()

            # Initialize colors
            self.theme_manager.initialize_colors()

            self._windows_created = True
            logger.info("UI setup complete")

        except Exception as e:
            logger.error(f"Failed to setup UI: {e}")
            raise UIError(f"UI setup failed: {e}") from e

    def teardown(self) -> None:
        """Clean up curses and restore terminal."""
        try:
            self.stdscr.keypad(False)
            curses.nocbreak()
            curses.echo()
            curses.endwin()
            logger.info("UI teardown complete")
        except Exception as e:
            logger.error(f"Error during teardown: {e}")

    def register_panel(self, panel_id: str, panel: BasePanel) -> None:
        """Register a panel with the UI manager.

        Args:
            panel_id: Unique panel identifier
            panel: Panel instance
        """
        self.panels[panel_id] = panel
        logger.debug(f"Registered panel: {panel_id}")

    def switch_panel(self, panel_id: str) -> None:
        """Switch to a different panel.

        Args:
            panel_id: ID of panel to switch to
        """
        if panel_id not in self.panels:
            logger.warning(f"Panel not found: {panel_id}")
            return

        # Deactivate current panel
        if self.active_panel:
            self.active_panel.deactivate()
            self.panel_history.append(self.active_panel.name)

        # Activate new panel
        self.active_panel = self.panels[panel_id]
        self.active_panel.activate()

        # Update breadcrumbs
        self.breadcrumbs.append(self.active_panel.name.title())
        if len(self.breadcrumbs) > 5:
            self.breadcrumbs = self.breadcrumbs[-5:]

        self.needs_redraw = True
        logger.debug(f"Switched to panel: {panel_id}")

    def go_back(self) -> bool:
        """Go back to previous panel in history.

        Returns:
            True if went back, False if at root
        """
        if not self.panel_history:
            return False

        prev_panel_name = self.panel_history.pop()
        for panel_id, panel in self.panels.items():
            if panel.name == prev_panel_name:
                if self.active_panel:
                    self.active_panel.deactivate()
                self.active_panel = panel
                self.active_panel.activate()
                if self.breadcrumbs:
                    self.breadcrumbs.pop()
                self.needs_redraw = True
                return True

        return False

    def handle_key(self, key: MappedKey) -> None:
        """Handle keyboard input.

        Args:
            key: Mapped keyboard input
        """
        # Global shortcuts
        if key == Key.CTRL_Q:
            self.is_running = False
            return

        if key == Key.CTRL_R:
            # Force full refresh
            self.stdscr.clear()
            self.stdscr.refresh()
            self.needs_redraw = True
            return

        if key == Key.ESC:
            # Go back
            if not self.go_back():
                # At root, show confirmation to quit
                pass
            return

        # Route to active panel
        if self.active_panel:
            handled = self.active_panel.on_key(key)
            if handled:
                self.needs_redraw = True

    def handle_key_code(self, key_code: int) -> None:
        """Handle raw key code.

        Args:
            key_code: Raw key code from curses
        """
        mapped_key = self.key_handler.map_key(key_code)
        self.handle_key(mapped_key)

    def handle_resize(self) -> None:
        """Handle terminal resize event."""
        try:
            height, width = self.stdscr.getmaxyx()
            self.layout.resize(height, width)
            self.needs_redraw = True
            logger.info(f"Terminal resized to {width}x{height}")
        except LayoutError as e:
            self.error_message = str(e)
            logger.error(f"Resize failed: {e}")

    def toggle_theme(self) -> None:
        """Toggle between dark and light themes."""
        self.theme_manager.toggle_theme()
        self.theme_manager.save_preference()
        self.needs_redraw = True
        logger.info(f"Switched to {self.theme_manager.current_theme.value} theme")

    def show_status(self, message: str, duration: float = 3.0) -> None:
        """Show a temporary status message.

        Args:
            message: Status message to display
            duration: How long to show message (seconds)
        """
        self.status_message = message
        self.status_message_time = time.time() + duration

    def show_error(self, message: str) -> None:
        """Show an error message.

        Args:
            message: Error message to display
        """
        self.error_message = message
        logger.error(f"UI Error: {message}")

    def render_header(self) -> None:
        """Render the header with agent status."""
        try:
            status = self.agent_controller.get_status()

            # Line 1: Model and status
            state_text = status.state.value.upper()
            model_text = f"{status.provider.upper()}: {status.model_name}"
            header_text = f" {state_text} │ {model_text} "

            attr = self.theme_manager.get_color_attr("header", bold=True)
            self.stdscr.addstr(0, 0, header_text.ljust(self.layout.total_width), attr)

            # Line 2: Cycle info and progress
            if status.total_cycles > 0:
                progress = status.current_cycle / status.total_cycles
                bar_width = 20
                filled = int(bar_width * progress)
                bar = "█" * filled + "░" * (bar_width - filled)
                cycle_text = f" Cycle: {status.current_cycle}/{status.total_cycles} [{bar}] "
            else:
                cycle_text = " Ready "

            self.stdscr.addstr(1, 0, cycle_text.ljust(self.layout.total_width), attr)

            # Line 3: Separator
            separator = "─" * self.layout.total_width
            self.stdscr.addstr(2, 0, separator, attr)

        except Exception as e:
            logger.error(f"Error rendering header: {e}")

    def render_footer(self) -> None:
        """Render the footer with breadcrumbs and key hints."""
        try:
            footer_y = self.layout.total_height - 2

            # Breadcrumbs
            breadcrumb_text = " > ".join(self.breadcrumbs)
            self.stdscr.addstr(
                footer_y,
                0,
                breadcrumb_text[:self.layout.total_width - 1],
                self.theme_manager.get_color_attr("normal"),
            )

            # Key hints
            hints_y = self.layout.total_height - 1
            hints = "ESC: Back │ Ctrl+Q: Quit │ Ctrl+R: Refresh │ 1-9: Panels"

            # Add panel-specific hints
            if self.active_panel:
                panel_hints = self._get_panel_hints(self.active_panel.name)
                if panel_hints:
                    hints += f" │ {panel_hints}"

            self.stdscr.addstr(
                hints_y,
                0,
                hints[:self.layout.total_width - 1],
                self.theme_manager.get_color_attr("info"),
            )

        except Exception as e:
            logger.error(f"Error rendering footer: {e}")

    def _get_panel_hints(self, panel_name: str) -> str:
        """Get context-specific key hints for a panel.

        Args:
            panel_name: Name of active panel

        Returns:
            Hint string for panel
        """
        hints_map = {
            "tasks": "N: New │ E: Edit │ D: Delete",
            "logs": "/: Search │ F: Filter │ C: Clear",
            "code": "E: Edit │ Enter: Open",
            "thinking": "Home/End: Jump",
        }
        return hints_map.get(panel_name, "")

    def render_sidebar(self) -> None:
        """Render the status sidebar."""
        try:
            status = self.agent_controller.get_status()
            sidebar = self.layout.get_sidebar_area()

            y_offset = 0
            attr = self.theme_manager.get_color_attr("status")

            # Title
            self.stdscr.addstr(
                sidebar.y + y_offset,
                sidebar.x,
                " STATUS ".center(sidebar.width),
                self.theme_manager.get_color_attr("status", bold=True),
            )
            y_offset += 2

            # Metrics
            metrics = [
                f"Thoughts: {status.thoughts_count}",
                f"Actions: {status.actions_count}",
                f"Duration: {int(status.session_duration_seconds)}s",
            ]

            if status.active_task_id:
                metrics.append(f"Task: #{status.active_task_id}")

            for metric in metrics:
                if y_offset < sidebar.height:
                    self.stdscr.addstr(
                        sidebar.y + y_offset,
                        sidebar.x,
                        metric[:sidebar.width],
                        attr,
                    )
                    y_offset += 1

        except Exception as e:
            logger.error(f"Error rendering sidebar: {e}")

    def render(self) -> None:
        """Perform full screen render."""
        try:
            start_time = time.perf_counter()

            # Clear screen
            self.stdscr.clear()

            # Render components
            self.render_header()
            self.render_sidebar()
            self.render_footer()

            # Render active panel
            if self.active_panel:
                self.active_panel.full_render()

            # Show status/error messages
            if self.status_message and time.time() < self.status_message_time:
                # Show in center
                msg_y = self.layout.total_height // 2
                msg_x = (self.layout.total_width - len(self.status_message)) // 2
                self.stdscr.addstr(
                    msg_y,
                    msg_x,
                    self.status_message,
                    self.theme_manager.get_color_attr("success", bold=True),
                )
            elif self.error_message:
                # Show error at bottom
                error_y = self.layout.total_height - 3
                self.stdscr.addstr(
                    error_y,
                    2,
                    f"ERROR: {self.error_message}"[:self.layout.total_width - 4],
                    self.theme_manager.get_color_attr("error", bold=True),
                )

            # Refresh
            self.stdscr.refresh()

            # Log performance
            render_time_ms = (time.perf_counter() - start_time) * 1000
            if render_time_ms > 50:
                logger.warning(f"Slow render: {render_time_ms:.1f}ms")

            self.needs_redraw = False

        except Exception as e:
            logger.error(f"Error during render: {e}")
            self.is_running = False

    def run(self) -> None:
        """Main event loop."""
        self.is_running = True

        try:
            while self.is_running:
                # Handle input
                try:
                    key_code = self.stdscr.getch()
                    if key_code != -1:
                        self.handle_key_code(key_code)
                except curses.error:
                    pass

                # Check for resize
                if curses.is_term_resized(*self.layout.__dict__.values()):
                    self.handle_resize()

                # Render if needed
                if self.needs_redraw:
                    self.render()

                # Small delay to avoid spinning
                time.sleep(0.01)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}")
            raise
        finally:
            self.teardown()
