# Architecture Overview

## Core Loops

- **AgentController** (`agent_cli/agent_controller.py`)
  - Runs on asyncio and exposes queues (`status_queue`, `thought_queue`, `log_queue`).
  - Normalises lifecycle changes (start, pause, resume, stop) into file-based commands consumed by the agent.
  - Guards against crashes and disconnections, ensuring the UI still receives meaningful status updates.

- **UIManager** (`agent_cli/ui_manager.py`)
  - Owns the curses surface, panel registry, breadcrumbs, and global key handling.
  - Ticks at up to 10 FPS. When the terminal is undersized it displays a warning rather than raising.
  - Persists panel state via `StateManager`, restoring scroll positions and selections on navigation.

## Panel System

All panels derive from `Panel` (`agent_cli/panels/base.py`) and share a consistent lifecycle:

1. `on_focus()` – mark panel active and request a render
2. `render()` – draw content within the allocated area using the shared `ThemeManager`
3. `handle_key()` – consume panel-specific shortcuts; returning `True` persists the state snapshot
4. `capture_state()` / `restore_state()` – lightweight persistence per panel

Implemented panels:

| Panel | Purpose |
|-------|---------|
| `HomePanel` | Dashboard summary of agent status, tasks, and logs |
| `TaskManagerPanel` | Persistent CRUD with activation and pagination |
| `ThinkingPanel` | Streaming reasoning feed with auto-scroll controls |
| `LogsPanel` | Real-time logs with filtering, search, save, and clear features |
| `CodeEditorPanel` | Project browser with basic editing, read-only detection, and save prompts |
| `ModelConfigPanel` | Model selection and parameter tuning with persisting config |
| `VerificationPanel` | Test suite runner with status icons, summaries, and persisted history |
| `HelpPanel` | Searchable keyboard shortcut reference |

## State Persistence

`StateManager` supports in-memory (for tests) or on-disk persistence per panel. It includes undo/redo stacks for future high-risk interactions.

Panel-specific data lives under `~/.agent_cli/`:

- `tasks.json`
- `logs/`
- `model_config.json`
- `test_results.json`

## Theming

`ThemeManager` ships dark/light palettes plus a monochrome fallback. The UI toggles between themes via the global `T` hotkey; panels simply request color tokens rather than hard-coding pairs.

## Error Handling Strategy

- Agent crashes trigger `_emit_status()` with `lifecycle_state="error"` while retaining connectivity cues.
- File parsing issues (e.g. corrupt `tasks.json`) fall back to empty states without raising.
- Terminal resize below 80x24 surfaces a banner instead of a stack trace.
- All risky operations funnel through helper methods that capture exceptions and surface user-facing notifications.

## Testing Approach

- `tests/conftest.py` supplies deterministic fakes for the curses screen, agent controller, and user interactions.
- Component tests validate keyboard flows, persistence, and edge cases (empty data, huge lists, corrupt files, disconnects).
- Async tests use `pytest.mark.asyncio` to exercise the controller queues.

