#!/usr/bin/env python3
"""Quick TUI launch test."""
import asyncio
import sys

from agent.tui.app import AgentTUI


async def test_launch():
    """Launch TUI and exit after 1 second."""
    app = AgentTUI()

    # Set a timer to exit
    async def auto_exit():
        await asyncio.sleep(1)
        print("\n✓ TUI launched successfully!")
        print(f"✓ Navigation entries: {len(app.navigation.entries)}")
        print(f"✓ Current focus index: {app.navigation.current_index}")
        focused = app.navigation.get_focused()
        if focused:
            print(f"✓ Focused widget: {focused.widget_id}")
        app.exit()

    asyncio.create_task(auto_exit())

    try:
        await app.run_async()
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(test_launch()))
