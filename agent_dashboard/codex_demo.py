"""Demo script to showcase Codex Dashboard features with sample data."""

import json
import time
from pathlib import Path
from datetime import datetime


def create_demo_thinking_events():
    """Create sample thinking events for demonstration."""
    thinking_file = Path("agent/state/thinking.jsonl")
    thinking_file.parent.mkdir(parents=True, exist_ok=True)

    events = [
        {
            "event_type": "cycle_start",
            "cycle": 1,
            "timestamp": time.time(),
            "data": {"cycle": 1}
        },
        {
            "event_type": "thinking",
            "cycle": 1,
            "timestamp": time.time() + 1,
            "data": {
                "type": "planning",
                "content": "Analyzing task requirements and determining optimal approach"
            }
        },
        {
            "event_type": "action",
            "cycle": 1,
            "timestamp": time.time() + 2,
            "data": {
                "action": "read_file",
                "details": "Reading pyproject.toml for dependency information",
                "status": "started"
            }
        },
        {
            "event_type": "action",
            "cycle": 1,
            "timestamp": time.time() + 3,
            "data": {
                "action": "read_file",
                "details": "Successfully read pyproject.toml (340 bytes)",
                "status": "completed"
            }
        },
        {
            "event_type": "thinking",
            "cycle": 1,
            "timestamp": time.time() + 4,
            "data": {
                "type": "analysis",
                "content": "Identified missing dependencies: textual, rich, pygments"
            }
        },
        {
            "event_type": "decision",
            "cycle": 1,
            "timestamp": time.time() + 5,
            "data": {
                "decision": "update_dependencies",
                "details": "Adding required packages to pyproject.toml dependencies list"
            }
        },
        {
            "event_type": "code_generation",
            "cycle": 1,
            "timestamp": time.time() + 6,
            "data": {
                "language": "python",
                "details": "Generated widget classes with complete implementations"
            }
        },
        {
            "event_type": "verification",
            "cycle": 1,
            "timestamp": time.time() + 7,
            "data": {
                "tool": "syntax_check",
                "result": "passed",
                "details": "All Python files compile without errors"
            }
        },
        {
            "event_type": "model_interaction",
            "cycle": 1,
            "timestamp": time.time() + 8,
            "data": {
                "model": "deepseek-coder:6.7b",
                "interaction_type": "code_completion",
                "details": "Generated 1847 tokens for widget implementations"
            }
        },
        {
            "event_type": "cycle_end",
            "cycle": 1,
            "timestamp": time.time() + 9,
            "data": {"cycle": 1}
        },
        {
            "event_type": "cycle_start",
            "cycle": 2,
            "timestamp": time.time() + 10,
            "data": {"cycle": 2}
        },
        {
            "event_type": "thinking",
            "cycle": 2,
            "timestamp": time.time() + 11,
            "data": {
                "type": "planning",
                "content": "Proceeding to integration testing of new Codex UI components"
            }
        },
        {
            "event_type": "action",
            "cycle": 2,
            "timestamp": time.time() + 12,
            "data": {
                "action": "run_tests",
                "details": "Executing pytest suite on new dashboard code",
                "status": "started"
            }
        },
        {
            "event_type": "thinking",
            "cycle": 2,
            "timestamp": time.time() + 13,
            "data": {
                "type": "evaluation",
                "content": "All tests passing, no syntax errors detected, ready for deployment"
            }
        },
        {
            "event_type": "action",
            "cycle": 2,
            "timestamp": time.time() + 14,
            "data": {
                "action": "run_tests",
                "details": "All 24 tests passed in 3.42s",
                "status": "completed"
            }
        },
    ]

    with open(thinking_file, 'w', encoding='utf-8') as f:
        for event in events:
            f.write(json.dumps(event) + '\n')

    print(f"Created demo thinking events at {thinking_file}")


def create_demo_task_file():
    """Create sample task file."""
    task_file = Path("agent/local/control/task.txt")
    task_file.parent.mkdir(parents=True, exist_ok=True)

    task_content = """Implement a modern Codex-style UI for the AI agent dashboard.

Requirements:
1. Use Textual framework for modern TUI
2. Dark theme with cyan/blue accents
3. Real-time streaming displays for AI thinking
4. Task management with add/delete/activate
5. Syntax highlighted code viewer
6. Live metrics and progress tracking

This is a comprehensive implementation with no placeholders or TODOs.
"""

    task_file.write_text(task_content, encoding='utf-8')
    print(f"Created demo task file at {task_file}")


def create_demo_config():
    """Create sample config file."""
    config_file = Path("agent/config.json")
    config_file.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "provider": {
            "type": "ollama",
            "model": "deepseek-coder:6.7b",
            "base_url": "http://localhost:11434"
        },
        "max_cycles": 0,
        "verification_enabled": True,
        "auto_commit": False
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    print(f"Created demo config file at {config_file}")


def main():
    """Run demo setup."""
    print("========================================")
    print("Codex Dashboard - Demo Setup")
    print("========================================")
    print("")
    print("This script creates sample data to demonstrate")
    print("the Codex dashboard features.")
    print("")

    create_demo_thinking_events()
    create_demo_task_file()
    create_demo_config()

    print("")
    print("========================================")
    print("Demo Setup Complete!")
    print("========================================")
    print("")
    print("Now launch the Codex dashboard:")
    print("")
    print("  agent --codex")
    print("")
    print("You'll see:")
    print("  - Sample thinking events in the AI stream")
    print("  - A demo task in the task panel")
    print("  - Config loaded from agent/config.json")
    print("")
    print("Try these actions:")
    print("  1. Press '2' to view AI thinking stream")
    print("  2. Press '1' to go back to tasks")
    print("  3. Add a new task and activate it")
    print("  4. Press 's' to start the agent")
    print("  5. Press 'q' to quit")
    print("")


if __name__ == "__main__":
    main()
