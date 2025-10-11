#!/usr/bin/env python3
"""Diagnose TUI issues."""

print("=== TUI Diagnostic ===\n")

# Check version
from agent import __version__

print(f"✓ Agent version: {__version__}")

# Check which TUI is being loaded
try:
    import inspect

    from agent.view import launch_tui

    source = inspect.getsource(launch_tui)
    print("\n✓ agent.view.launch_tui source:")
    for line in source.split('\n')[:10]:
        print(f"  {line}")

    if "simple_app" in source:
        print("\n✗ ERROR: Still using simple_app!")
        print("  Expected: from .tui.app import launch_app")
        print("  Found: from .tui.simple_app import launch_simple_tui")
    elif "launch_app" in source:
        print("\n✓ Correctly using launch_app from tui.app")

except Exception as e:
    print(f"\n✗ Error importing: {e}")

# Check TUI app
try:
    from agent.tui.app import AgentTUI
    print("\n✓ Can import AgentTUI")

    app = AgentTUI()

    # Check CSS
    css_path = app.CSS_PATH
    print(f"\n✓ CSS path: {css_path}")
    print(f"✓ CSS exists: {css_path.exists()}")

    if css_path.exists():
        content = css_path.read_text()
        if "heavy yellow" in content:
            print("✓ CSS has new focus styling (heavy yellow)")
        else:
            print("✗ CSS missing new focus styling!")

    # Check navigation
    entries = app._build_navigation_order()
    print(f"\n✓ Navigation has {len(entries)} entries")

    # Check if test data loaded
    from agent.tui.state_watcher import StateWatcher
    watcher = StateWatcher()
    snapshot = watcher.snapshot()
    print("\n✓ State snapshot:")
    print(f"  Tasks: {len(snapshot.tasks)}")
    print(f"  Gates: {len(snapshot.gates)}")
    print(f"  Artifacts: {len(snapshot.artifacts)}")

    if len(snapshot.tasks) == 0:
        print("\n  Note: No tasks loaded yet. TUI will auto-generate on first launch.")

except Exception as e:
    print(f"\n✗ Error with AgentTUI: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Diagnostic Complete ===")
