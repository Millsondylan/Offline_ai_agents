"""Main entry point for agent control panel."""

import curses
import logging
import sys
from pathlib import Path

from agent_control_panel.core.agent_controller import AgentController
from agent_control_panel.core.state_manager import StateManager
from agent_control_panel.core.ui_manager import UIManager, UIError
from agent_control_panel.panels.home_panel import HomePanel
from agent_control_panel.panels.task_panel import TaskPanel
from agent_control_panel.panels.thinking_panel import ThinkingPanel
from agent_control_panel.panels.logs_panel import LogsPanel
from agent_control_panel.panels.help_panel import HelpPanel


# Setup logging
log_file = Path.home() / ".agent_cli" / "control_panel.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr),
    ],
)

logger = logging.getLogger(__name__)


def main_curses(stdscr):
    """Main curses application.

    Args:
        stdscr: Curses standard screen
    """
    try:
        # Initialize components
        agent_controller = AgentController()
        state_manager = StateManager()

        # Create UI manager
        ui_manager = UIManager(stdscr, agent_controller, state_manager)
        ui_manager.setup()

        # Create panels
        home_panel = HomePanel(
            stdscr,
            agent_controller,
            state_manager,
        )
        task_panel = TaskPanel(stdscr, state_manager)
        thinking_panel = ThinkingPanel(
            stdscr,
            agent_controller,
            state_manager,
        )
        logs_panel = LogsPanel(
            stdscr,
            agent_controller,
            ui_manager.theme_manager,
            state_manager,
        )
        help_panel = HelpPanel(stdscr, state_manager)

        # Register panels
        ui_manager.register_panel("home", home_panel)
        ui_manager.register_panel("tasks", task_panel)
        ui_manager.register_panel("thinking", thinking_panel)
        ui_manager.register_panel("logs", logs_panel)
        ui_manager.register_panel("help", help_panel)

        # Set initial panel
        ui_manager.switch_panel("home")

        # Run main loop
        ui_manager.run()

    except UIError as e:
        logger.error(f"UI Error: {e}")
        print(f"\nError: {e}", file=sys.stderr)
        print("Terminal must be at least 80x24", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.exception("Fatal error")
        print(f"\nFatal error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Entry point for the application."""
    try:
        curses.wrapper(main_curses)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nExiting...")
    except Exception as e:
        logger.exception("Unhandled exception")
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
