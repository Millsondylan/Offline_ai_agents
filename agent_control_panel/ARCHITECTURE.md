# Agent Control Panel - Architecture

## Overview

Production-grade, test-driven CLI control panel for autonomous AI agents built with Python curses.

## Design Principles

1. **Test-Driven Development**: All tests written before implementation
2. **Zero Crashes**: Graceful error handling at every layer
3. **Performance**: <50ms input latency, <100ms update latency
4. **Type Safety**: Full type annotations with mypy
5. **Production Ready**: No TODOs, no placeholders

## Architecture Layers

### Layer 1: Core Infrastructure

#### `core/models.py`
- Type-safe data models using Python dataclasses
- Enums for all state values
- Zero runtime overhead

#### `core/theme_manager.py`
- Dark/light theme support
- Graceful fallback to monochrome
- Persistent theme preference

#### `utils/keyboard.py`
- Normalized key handling across terminals
- Escape sequence detection
- Type-safe key mappings

#### `utils/layout.py`
- Responsive layout calculations
- Minimum terminal size enforcement (80x24)
- Dynamic sidebar sizing

### Layer 2: State & Communication

#### `core/state_manager.py`
- Persistent state with JSON serialization
- Undo/redo with configurable history
- Thread-safe concurrent access
- Atomic saves to prevent corruption

#### `core/agent_controller.py`
- Non-blocking agent communication
- Thread-safe message queues
- Automatic reconnection support
- Graceful crash detection

### Layer 3: UI Framework

#### `core/ui_manager.py`
**Main controller** managing:
- Panel lifecycle
- Keyboard routing
- Screen rendering
- Theme application
- Breadcrumb navigation

**Responsibilities:**
- Initialize curses environment
- Route input to active panel
- Render header/footer/sidebar
- Handle terminal resize
- Coordinate real-time updates

#### `panels/base_panel.py`
**Abstract base** providing:
- Common rendering utilities
- Scroll state management
- Error boundary handling
- Safe curses operations

### Layer 4: Panels

Each panel implements `BasePanel`:

1. **HomePanel** - Dashboard overview
2. **TaskPanel** - CRUD task management
3. **ThinkingPanel** - Live agent reasoning stream
4. **LogsPanel** - Colored, filterable execution logs
5. **HelpPanel** - Keyboard shortcuts reference

## Data Flow

```
User Input
    ↓
KeyHandler → map to MappedKey
    ↓
UIManager.handle_key()
    ↓
    ├─→ Global shortcuts (Ctrl+Q, ESC)
    └─→ Active Panel.handle_key()
            ↓
        Panel updates state
            ↓
        UIManager.needs_redraw = True
            ↓
        UIManager.render()
            ↓
        Screen updates
```

## Agent Communication

```
Agent Process
    ↓
    ├─→ Thoughts → thought_queue → ThinkingPanel
    ├─→ Logs    → log_queue     → LogsPanel
    └─→ Status  → polled        → Header/Sidebar

AgentController (thread-safe queues)
    ↓
Panel subscribers notified
    ↓
UI updates on next render cycle
```

## Error Handling Strategy

### Never Crash Principle

Every exception caught and handled:

```python
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Error: {e}")
    ui.show_error("User-friendly message")
    # Continue operation
except Exception as e:
    logger.exception("Unexpected error")
    # Still don't crash
```

### Error Categories

1. **Agent Errors** → Show in sidebar, keep UI running
2. **File Errors** → Show dialog, offer retry
3. **Rendering Errors** → Catch in panel, show error text
4. **Terminal Errors** → Fallback to safe mode or exit gracefully

## Performance Optimizations

### Rendering
- Only redraw when `needs_redraw = True`
- Partial updates for status changes
- Bounded queue sizes (prevent memory leaks)
- Lazy rendering of off-screen content

### Input
- Non-blocking `getch()` with 10ms sleep
- Debounced resize handling
- Direct panel routing (no event system overhead)

### Memory
- Fixed-size deques for thoughts (1000) and logs (5000)
- Bounded undo history (50 entries)
- Periodic state persistence (not on every change)

## Thread Safety

### Protected Resources

- `AgentController._lock`: Guards agent state
- `StateManager._lock`: Guards state dictionary
- Message queues: Thread-safe `deque` with `maxlen`

### Lock-Free Design

- UI runs in main thread only
- Agent callbacks append to queues
- Subscribers invoked in controller thread
- No locks needed in UI code path

## Testing Strategy

### Unit Tests (Phase 1 & 2)
- All core components
- Mock curses with MagicMock
- Deterministic fixtures

### Integration Tests (Phase 4)
- Full UI lifecycle
- Multi-panel workflows
- State persistence
- Agent interaction

### Performance Tests
- Render time <50ms
- Input latency <50ms
- Memory bounds verified

## File Structure

```
agent_control_panel/
├── __init__.py
├── __main__.py              # Entry point
├── core/
│   ├── __init__.py
│   ├── models.py           # Data models
│   ├── theme_manager.py    # Themes
│   ├── ui_manager.py       # Main controller
│   ├── agent_controller.py # Agent comms
│   └── state_manager.py    # State persistence
├── panels/
│   ├── __init__.py
│   ├── base_panel.py       # Abstract base
│   ├── home_panel.py       # Dashboard
│   ├── task_panel.py       # Tasks
│   ├── thinking_panel.py   # Thoughts
│   ├── logs_panel.py       # Logs
│   └── help_panel.py       # Help
├── utils/
│   ├── __init__.py
│   ├── keyboard.py         # Input handling
│   └── layout.py           # Layout math
└── tests/
    ├── conftest.py         # Shared fixtures
    ├── test_*.py           # Unit tests
    └── test_integration.py # Integration tests
```

## Extension Points

### Adding New Panels

1. Create `panels/new_panel.py` extending `BasePanel`
2. Implement `handle_key()` and `render()`
3. Register in `__main__.py`
4. Add keyboard shortcut in `UIManager`

### Custom Themes

1. Add color definitions to `ThemeManager`
2. Register color pairs in `initialize_colors()`
3. Use via `theme_manager.get_color_attr(name)`

### State Persistence

1. Use `state_manager.set(key, value)` to store
2. Use `state_manager.get(key)` to retrieve
3. Automatic save on `state_manager.save()`

## Dependencies

**Runtime:**
- Python 3.10+
- curses (built-in)

**Development:**
- pytest
- pytest-asyncio
- pytest-cov
- black
- ruff
- mypy

## Build & Distribution

```bash
# Development
pip install -e .[dev]

# Production
pip install agent-control-panel

# Run
python -m agent_control_panel
```

## Logging

All logs written to `~/.agent_cli/control_panel.log`

Log levels:
- DEBUG: Detailed diagnostics
- INFO: Normal operations
- WARNING: Recoverable issues
- ERROR: Handled errors
- CRITICAL: Should-never-happen events
