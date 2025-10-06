"""Main dashboard UI controller."""

import curses
import time
from typing import Optional

from agent_dashboard.core.real_agent_manager import RealAgentManager
from agent_dashboard.core.theme import ThemeManager
from agent_dashboard.core.models import AgentStatus

from agent_dashboard.panels.home import HomePanel
from agent_dashboard.panels.tasks import TaskPanel
from agent_dashboard.panels.thinking import ThinkingPanel
from agent_dashboard.panels.logs import LogsPanel
from agent_dashboard.panels.help import HelpPanel
from agent_dashboard.panels.code_viewer import CodeViewerPanel
from agent_dashboard.panels.model_config import ModelConfigPanel


class Dashboard:
    """Main dashboard UI controller."""

    MENU_ITEMS = [
        "T. Task Manager",
        "S. Start/Pause",
        "X. Stop Agent",
        "A. AI Thinking",
        "L. Logs",
        "C. Code Viewer",
        "M. Model Config",
        "V. Verification",
        "H. Help",
        "Q. Exit",
    ]

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.agent_manager = RealAgentManager()
        self.theme_manager = ThemeManager()

        # Initialize panels
        self.panels = {
            'home': HomePanel(self.agent_manager, self.theme_manager),
            'tasks': TaskPanel(self.agent_manager, self.theme_manager),
            'thinking': ThinkingPanel(self.agent_manager, self.theme_manager),
            'logs': LogsPanel(self.agent_manager, self.theme_manager),
            'help': HelpPanel(self.agent_manager, self.theme_manager),
            'code': CodeViewerPanel(self.agent_manager, self.theme_manager),
            'model': ModelConfigPanel(self.agent_manager, self.theme_manager),
        }

        self.current_panel = 'home'
        self.breadcrumbs = ["Home"]
        self.running = True

        # Setup curses
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(100)
        self.theme_manager.initialize()

    def run(self):
        """Main event loop."""
        last_update = time.time()

        while self.running:
            try:
                # Get terminal size
                height, width = self.stdscr.getmaxyx()

                # Clear screen
                self.stdscr.clear()

                # Render UI
                self.render_header(width)
                self.render_layout(height, width)
                self.render_footer(height, width)

                # Refresh
                self.stdscr.refresh()

                # Handle input
                key = self.stdscr.getch()
                if key != -1:
                    self.handle_key(key)

                # Throttle updates
                time.sleep(0.05)

            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                # Don't crash on errors
                pass

    def render_header(self, width: int):
        """Render header bar."""
        state = self.agent_manager.get_state()

        # Line 1: Model, Session, Cycle, Status
        line1 = f" Model: {state.model}   Session: {state.session_id}   " \
                f"Cycle: #{state.cycle} ({state.status.value})   " \
                f"Elapsed: {state.elapsed_seconds}s"
        self.stdscr.addstr(0, 0, line1[:width].ljust(width),
                          self.theme_manager.get('header') | curses.A_BOLD)

        # Line 2: Status, Mode, Progress
        progress_bar = self._make_progress_bar(state.progress_percent, 20)
        line2 = f" Status: {state.status.value}   Mode: {state.mode.value}   " \
                f"Progress: {progress_bar} {state.progress_percent}%"
        self.stdscr.addstr(1, 0, line2[:width].ljust(width),
                          self.theme_manager.get('header'))

        # Line 3: Separator
        self.stdscr.addstr(2, 0, "─" * width, self.theme_manager.get('normal'))

    def render_layout(self, height: int, width: int):
        """Render main layout with menu, content, and sidebar."""
        content_start = 3
        content_height = height - 5  # Header(3) + Footer(2)

        # Calculate widths
        menu_width = 17
        sidebar_width = 24
        content_width = width - menu_width - sidebar_width - 2

        # Render menu
        self.render_menu(content_start, 0, content_height, menu_width)

        # Render vertical separator
        for y in range(content_start, content_start + content_height):
            self.stdscr.addstr(y, menu_width, "│", self.theme_manager.get('normal'))

        # Render content panel
        panel = self.panels.get(self.current_panel)
        if panel:
            panel.render(self.stdscr, content_start, menu_width + 1,
                        content_height, content_width)

        # Render vertical separator
        for y in range(content_start, content_start + content_height):
            try:
                self.stdscr.addstr(y, width - sidebar_width - 1, "│",
                                 self.theme_manager.get('normal'))
            except curses.error:
                pass

        # Render sidebar
        self.render_sidebar(content_start, width - sidebar_width,
                          content_height, sidebar_width)

    def render_menu(self, start_y: int, start_x: int, height: int, width: int):
        """Render menu."""
        y = start_y + 1
        x = start_x + 1

        self.stdscr.addstr(y, x, "** Main Menu **",
                          self.theme_manager.get('highlight') | curses.A_BOLD)
        y += 1

        for i, item in enumerate(self.MENU_ITEMS):
            if y >= start_y + height:
                break

            # Highlight current section
            attr = self.theme_manager.get('selected') if self._is_current_menu(i) else curses.A_NORMAL

            self.stdscr.addstr(y, x, item[:width-2], attr)
            y += 1

    def render_sidebar(self, start_y: int, start_x: int, height: int, width: int):
        """Render status sidebar."""
        state = self.agent_manager.get_state()

        y = start_y + 1
        x = start_x + 1

        # Title
        self.stdscr.addstr(y, x, "** Agent Status **",
                          self.theme_manager.get('highlight') | curses.A_BOLD)
        y += 2

        # Status indicator
        status_color = {
            AgentStatus.RUNNING: 'running',
            AgentStatus.PAUSED: 'warning',
            AgentStatus.STOPPED: 'error',
            AgentStatus.IDLE: 'normal',
        }.get(state.status, 'normal')

        self.stdscr.addstr(y, x, f"● Status: {state.status.value}",
                          self.theme_manager.get(status_color) | curses.A_BOLD)
        y += 2

        # Current task
        if state.current_task:
            self.stdscr.addstr(y, x, "● Current Task:")
            y += 1
            task_text = f"  {state.current_task[:18]}"
            self.stdscr.addstr(y, x, task_text)
        else:
            self.stdscr.addstr(y, x, "● No active task")
        y += 2

        # Metrics
        self.stdscr.addstr(y, x, f"● Cycle: {state.cycle}/{state.max_cycles}")
        y += 1
        self.stdscr.addstr(y, x, f"● Elapsed: {state.elapsed_seconds}s")
        y += 1
        self.stdscr.addstr(y, x, f"● Mode: {state.mode.value}")
        y += 1
        self.stdscr.addstr(y, x, f"● Model: {state.model[:10]}")
        y += 2

        # Errors/Warnings
        if state.errors > 0:
            self.stdscr.addstr(y, x, f"● Errors: {state.errors}",
                             self.theme_manager.get('error'))
            y += 1
        if state.warnings > 0:
            self.stdscr.addstr(y, x, f"● Warnings: {state.warnings}",
                             self.theme_manager.get('warning'))

    def render_footer(self, height: int, width: int):
        """Render footer with breadcrumbs and hints."""
        footer_y = height - 2

        # Breadcrumbs
        breadcrumb = " › ".join(self.breadcrumbs)
        self.stdscr.addstr(footer_y, 0, "─" * width, self.theme_manager.get('normal'))
        self.stdscr.addstr(footer_y + 1, 1, f"Breadcrumb: {breadcrumb[:width-15]}",
                          self.theme_manager.get('info'))

        # Hints
        hints = "T/S/A/L/C/M/H = Menu | ↑/↓ = Navigate | Enter = Select | ESC = Back | F1 = Theme | Q = Quit"
        hint_y = height - 1
        self.stdscr.addstr(hint_y, 1, f"Hint: {hints[:width-8]}",
                          self.theme_manager.get('info'))

    def handle_key(self, key: int):
        """Handle keyboard input."""
        # Global shortcuts
        if key in (ord('q'), ord('Q')):
            self.running = False
            return

        elif key == curses.KEY_F1:  # F1 for theme toggle
            self.theme_manager.toggle()
            return

        elif key == 27:  # ESC
            if len(self.breadcrumbs) > 1:
                self.breadcrumbs.pop()
                self.current_panel = 'home'
            return

        # Menu shortcuts (letter-based)
        elif key in (ord('t'), ord('T')):
            self.switch_panel('tasks', "Task Manager")
            return

        elif key in (ord('s'), ord('S')):
            self.handle_start_pause()
            return

        elif key in (ord('x'), ord('X')):
            self.agent_manager.stop()
            return

        elif key in (ord('a'), ord('A')):
            self.switch_panel('thinking', "AI Thinking")
            return

        elif key in (ord('l'), ord('L')):
            self.switch_panel('logs', "Logs")
            return

        elif key in (ord('c'), ord('C')):
            self.switch_panel('code', "Code Viewer")
            return

        elif key in (ord('m'), ord('M')):
            self.switch_panel('model', "Model Config")
            return

        elif key in (ord('h'), ord('H')):
            self.switch_panel('help', "Help")
            return

        elif key == ord(' '):  # Space for quick pause/resume
            self.handle_start_pause()
            return

        # Delegate to active panel
        panel = self.panels.get(self.current_panel)
        if panel:
            panel.handle_key(key)

    def handle_start_pause(self):
        """Handle start/pause toggle."""
        state = self.agent_manager.get_state()

        if state.status == AgentStatus.IDLE or state.status == AgentStatus.STOPPED:
            self.agent_manager.start()
        elif state.status == AgentStatus.RUNNING:
            self.agent_manager.pause()
        elif state.status == AgentStatus.PAUSED:
            self.agent_manager.resume()

    def switch_panel(self, panel_name: str, display_name: str):
        """Switch to a different panel."""
        self.current_panel = panel_name
        if display_name not in self.breadcrumbs:
            self.breadcrumbs.append(display_name)

    def _is_current_menu(self, index: int) -> bool:
        """Check if menu item corresponds to current panel."""
        mapping = {
            0: 'tasks',
            3: 'thinking',
            4: 'logs',
            8: 'help',
        }
        return mapping.get(index) == self.current_panel

    def _make_progress_bar(self, percent: int, width: int) -> str:
        """Make a progress bar."""
        filled = int((percent / 100) * width)
        return "[" + "█" * filled + "░" * (width - filled) + "]"
