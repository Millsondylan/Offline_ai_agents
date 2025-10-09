"""Main entry point for agent dashboard."""

import curses
import sys
import logging
from pathlib import Path

from agent_dashboard.dashboard import Dashboard
from agent_dashboard.core.model_downloader import ModelDownloader


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
        # Ensure model is available before starting dashboard
        print("=== Agent Dashboard Startup ===")
        print("Checking for available models...")

        model = ModelDownloader.ensure_model_available()
        if model:
            ModelDownloader.configure_agent_for_ollama(model)
            print(f"\n✓ Ready to start with model: {model}")
        else:
            print("\n⚠ No model available. You can:")
            print("1. Install Ollama: brew install ollama")
            print("2. Download a model: ollama pull deepseek-coder:33b")
            print("3. Set API keys: export ANTHROPIC_API_KEY=...")
            print("\nContinuing anyway (configure model in dashboard)...")

        print("\nStarting dashboard...")
        try:
            curses.wrapper(main_curses)
        except curses.error as e:
            print(f"\nCurses interface failed: {e}", file=sys.stderr)
            print("Falling back to simple CLI interface...", file=sys.stderr)
            from agent_dashboard.simple_cli import SimpleCLI
            cli = SimpleCLI()
            cli.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
