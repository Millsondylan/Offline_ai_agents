"""Main entry point for agent dashboard."""

import curses
import sys
import logging
from pathlib import Path

from agent_dashboard.dashboard import Dashboard


# Setup logging
log_dir = Path.home() / ".agent_cli"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "dashboard.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
    ],
)

logger = logging.getLogger(__name__)


def main_curses(stdscr):
    """Main curses application."""
    try:
        dashboard = Dashboard(stdscr)
        dashboard.run()
    except Exception as e:
        logger.exception("Fatal error in dashboard")
        raise


def main():
    """Entry point."""
    try:
        curses.wrapper(main_curses)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
