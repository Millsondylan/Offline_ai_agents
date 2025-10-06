# Agent CLI Control Panel

A curses-based control panel for supervising autonomous AI agents. The interface focuses on reliability, keyboard-only workflows, and real-time visibility into the agent state.

## Features

- Multi-panel layout covering dashboard, task management, thinking stream, logs, code editing, model configuration, verification, and contextual help
- Async agent controller with status, thought, and log queues
- Persistent state management with undo/redo support
- Dark/light theming with monochrome fallback
- Production-grade error handling that keeps the UI responsive even when the agent fails

## Quick Start

1. Install dependencies from `pyproject.toml` (e.g. `pip install -r requirements.txt` or `pip install -e .[dev]`).
2. Export any necessary environment variables (see `.env.example`).
3. Run the CLI entry point (to be integrated with your launcher) and navigate using the numeric hotkeys and arrow keys.

## Running Tests

```
python -m pytest tests
```

The suite relies on deterministic fakes and does not require a live agent process.

## Directory Layout

- `agent_cli/agent_controller.py` – async bridge to the agent runtime
- `agent_cli/ui_manager.py` – curses compositor and input router
- `agent_cli/panels/` – individual panel implementations
- `agent_cli/state_manager.py` – persistence and undo/redo
- `agent_cli/theme.py` – theme definitions
- `tests/` – TDD suite covering all components

## Configuration

Default file locations resolve under `~/.agent_cli/`. Sample settings are bundled in `agent_cli/config/default_settings.json`.

## Keyboard Reference

Open the Help panel (hotkey `8` by default) for a searchable list of shortcuts.

