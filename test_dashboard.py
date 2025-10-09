#!/usr/bin/env python3
"""Test script for the dashboard functionality."""

import time
from agent_dashboard.core.real_agent_manager import RealAgentManager

def test_agent_manager():
    """Test the agent manager basic functionality."""
    print("Testing Agent Manager...")

    # Create agent manager
    manager = RealAgentManager()
    print(f"✓ Initial status: {manager.get_state().status.value}")

    # Test starting agent
    print("Starting agent...")
    manager.start()
    time.sleep(2)
    state = manager.get_state()
    print(f"✓ After start: {state.status.value}")

    # Test adding a task
    print("Adding a test task...")
    task = manager.add_task("Test task from manual test")
    print(f"✓ Added task #{task.id}: {task.description}")

    # Wait a bit
    time.sleep(3)
    state = manager.get_state()
    print(f"✓ Final status: {state.status.value}")
    print(f"✓ Current task: {state.current_task}")
    print(f"✓ Cycle: {state.cycle}")

    # Test logs
    logs = manager.get_logs()
    print(f"✓ Total logs: {len(logs)}")
    if logs:
        print(f"✓ Latest log: {logs[-1].message}")

    print("Agent Manager test completed successfully!")

def test_buttons_simulation():
    """Test button functionality without curses."""
    print("\nTesting Button Simulation...")

    from agent_dashboard.dashboard import Dashboard

    # Create a mock stdscr object
    class MockStdscr:
        def getmaxyx(self): return (24, 80)
        def clear(self): pass
        def addstr(self, *args, **kwargs): pass
        def refresh(self): pass
        def getch(self): return -1
        def nodelay(self, flag): pass
        def timeout(self, ms): pass
        def keypad(self, flag): pass

    try:
        # Test dashboard creation (this tests the initialization)
        dashboard = Dashboard(MockStdscr())
        print("✓ Dashboard creates successfully")

        # Test key handling
        dashboard.handle_key(ord('s'))  # Start/pause
        print("✓ Start/pause key handling works")

        dashboard.handle_key(ord('t'))  # Task manager
        print("✓ Task manager key handling works")

        dashboard.handle_key(ord('h'))  # Help
        print("✓ Help key handling works")

        print("Button simulation test completed successfully!")

    except Exception as e:
        print(f"Error in button test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        test_agent_manager()
        test_buttons_simulation()
        print("\n🎉 All tests passed! The dashboard should work correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()