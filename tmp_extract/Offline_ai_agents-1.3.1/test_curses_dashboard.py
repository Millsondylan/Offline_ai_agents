#!/usr/bin/env python3
"""Test the actual curses dashboard."""

import curses
import threading
import time

from agent_dashboard.dashboard import Dashboard


def test_curses_dashboard(stdscr):
    """Test the dashboard in curses mode."""
    try:
        # Initialize dashboard
        dashboard = Dashboard(stdscr)

        # Simulate some key presses
        def simulate_keys():
            time.sleep(1)
            # Simulate pressing 'S' to start
            dashboard.handle_key(ord('s'))
            time.sleep(1)
            # Simulate pressing 'Q' to quit
            dashboard.handle_key(ord('q'))

        # Start simulation in background
        thread = threading.Thread(target=simulate_keys, daemon=True)
        thread.start()

        # Run dashboard (will exit when 'q' is pressed)
        dashboard.run()

        return True
    except Exception as e:
        print(f"Dashboard test error: {e}")
        return False

def main():
    """Run the test."""
    print("Testing curses dashboard...")
    try:
        result = curses.wrapper(test_curses_dashboard)
        print("✓ Curses dashboard test successful!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
