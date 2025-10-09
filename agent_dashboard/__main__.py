"""Main entry point for agent dashboard."""

import argparse
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


def run_real_agent():
    """Run the autonomous file-editing agent."""
    try:
        print("=== Autonomous AI Agent ===")
        print("Checking for available models...")

        model = ModelDownloader.ensure_model_available()
        if model:
            ModelDownloader.configure_agent_for_ollama(model)
            print(f"✓ Using model: {model}")
        else:
            print("⚠ No model available. Please install Ollama and download a model:")
            print("  brew install ollama")
            print("  ollama pull deepseek-coder:6.7b")
            sys.exit(1)

        print("\nStarting autonomous agent...")
        print("The agent will:")
        print("  • Read tasks from agent/local/control/task.txt")
        print("  • Edit files in your current directory")
        print("  • Apply patches and make git commits")
        print("  • Run verification checks")
        print("\nPress Ctrl+C to stop.\n")

        # Import and run the real agent
        from agent.run import AgentLoop, load_config
        from pathlib import Path

        repo_root = Path.cwd()
        config_path = repo_root / "agent" / "config.json"

        if not config_path.exists():
            print(f"Error: Config file not found at {config_path}")
            print("Please run this command from the root of your project with agent/config.json")
            sys.exit(1)

        cfg = load_config(config_path)
        agent_loop = AgentLoop(repo_root, cfg)
        agent_loop.run()

    except KeyboardInterrupt:
        print("\nAgent stopped by user.")
    except Exception as e:
        print(f"\nAgent error: {e}", file=sys.stderr)
        sys.exit(1)


def run_dashboard():
    """Run the agent dashboard."""
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


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous AI Agent - Edit files and apply patches automatically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agent                    # Run autonomous agent (default)
  agent --dashboard        # Run monitoring dashboard
  agent --version          # Show version info

The autonomous agent reads tasks from agent/local/control/task.txt and
edits files in your current directory automatically.
        """)

    parser.add_argument('--dashboard', action='store_true',
                       help='Run the monitoring dashboard instead of the autonomous agent')
    parser.add_argument('--version', action='store_true',
                       help='Show version information')

    args = parser.parse_args()

    if args.version:
        try:
            import agent
            print(f"Agent version: {agent.__version__}")
        except:
            print("Agent version: unknown")
        return

    if args.dashboard:
        run_dashboard()
    else:
        run_real_agent()


if __name__ == "__main__":
    main()
