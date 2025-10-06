# Comprehensive Testing Plan

## Test-Driven Development Workflow

For each component, we follow this strict process:
1. **Write tests first** covering happy path, edge cases, and error conditions
2. **Run tests** (they should fail)
3. **Implement** minimum code to pass tests
4. **Refactor** for clarity and performance
5. **Verify** all tests still pass

## Phase 1: Core UI Framework Tests

### test_theme_manager.py
- [ ] Test dark theme color initialization
- [ ] Test light theme color initialization
- [ ] Test theme toggle switches correctly
- [ ] Test monochrome fallback when colors unavailable
- [ ] Test color pair registration
- [ ] Test theme persistence across restarts

### test_ui_manager.py
- [ ] Test initialization with 80x24 terminal
- [ ] Test initialization with 200x60 terminal
- [ ] Test initialization fails gracefully on too-small terminal (< 80x24)
- [ ] Test curses setup and teardown
- [ ] Test keyboard routing to active panel
- [ ] Test panel switching updates breadcrumbs
- [ ] Test header rendering with agent status
- [ ] Test footer rendering with key hints
- [ ] Test status sidebar updates
- [ ] Test window resize handling
- [ ] Test theme toggle applies to all elements
- [ ] Test render performance (< 50ms per frame)
- [ ] Test graceful shutdown on exception

### test_base_panel.py
- [ ] Test panel initialization
- [ ] Test panel activation/deactivation
- [ ] Test panel key handling delegation
- [ ] Test panel scroll state persistence
- [ ] Test panel render boundaries
- [ ] Test panel focus management

### test_keyboard.py
- [ ] Test number key (1-9) mapping
- [ ] Test arrow key mapping
- [ ] Test special key mapping (Enter, ESC, etc.)
- [ ] Test key code normalization
- [ ] Test invalid key handling

### test_layout.py
- [ ] Test header height calculation
- [ ] Test content area calculation
- [ ] Test sidebar width calculation
- [ ] Test footer height calculation
- [ ] Test window splitting for multi-column layouts
- [ ] Test layout adjustments on resize

## Phase 2: Agent Integration Tests

### test_agent_controller.py
- [ ] Test agent start/pause/stop operations
- [ ] Test agent status polling
- [ ] Test thought stream subscription
- [ ] Test log stream subscription
- [ ] Test agent crash detection
- [ ] Test automatic reconnection
- [ ] Test message queue thread safety
- [ ] Test async event handling
- [ ] Test graceful shutdown

### test_state_manager.py
- [ ] Test state persistence to disk
- [ ] Test state loading from disk
- [ ] Test state restoration after crash
- [ ] Test undo operation
- [ ] Test redo operation
- [ ] Test undo/redo stack limits
- [ ] Test concurrent state updates
- [ ] Test invalid state file handling

## Phase 3: Panel Tests

### test_home_panel.py
- [ ] Test dashboard rendering with all metrics
- [ ] Test progress bar visualization
- [ ] Test quick action buttons
- [ ] Test status summary display

### test_task_panel.py
- [ ] Test empty task list display
- [ ] Test task list rendering
- [ ] Test task creation via dialog
- [ ] Test task editing
- [ ] Test task deletion with confirmation
- [ ] Test task activation
- [ ] Test task filtering by status
- [ ] Test task sorting by priority
- [ ] Test pagination with 100+ tasks
- [ ] Test keyboard navigation (up/down)
- [ ] Test persistence to disk

### test_thinking_panel.py
- [ ] Test empty thoughts display
- [ ] Test thought streaming (real-time)
- [ ] Test auto-scroll to bottom
- [ ] Test manual scroll disables auto-scroll
- [ ] Test return to bottom re-enables auto-scroll
- [ ] Test thought formatting (multi-line)
- [ ] Test 1000+ thoughts without memory leak
- [ ] Test pause indicator when agent paused

### test_logs_panel.py
- [ ] Test empty logs display
- [ ] Test log rendering with color coding
- [ ] Test ERROR logs in red
- [ ] Test WARN logs in yellow
- [ ] Test INFO logs in white
- [ ] Test filter by level (errors only)
- [ ] Test search functionality
- [ ] Test search result highlighting
- [ ] Test save logs to file
- [ ] Test clear logs with confirmation
- [ ] Test 5000+ logs performance

### test_code_panel.py
- [ ] Test file list rendering
- [ ] Test file selection
- [ ] Test file content display with line numbers
- [ ] Test syntax highlighting (basic)
- [ ] Test edit mode activation
- [ ] Test cursor movement
- [ ] Test text insertion
- [ ] Test text deletion
- [ ] Test save to disk
- [ ] Test unsaved changes warning
- [ ] Test readonly file indicator
- [ ] Test large file (10,000+ lines) pagination

### test_model_panel.py
- [ ] Test model list display
- [ ] Test current model indicator
- [ ] Test model selection
- [ ] Test parameter adjustment (temperature, etc.)
- [ ] Test parameter validation
- [ ] Test reset to defaults
- [ ] Test config persistence

### test_verify_panel.py
- [ ] Test test list display
- [ ] Test run all tests
- [ ] Test run single test
- [ ] Test progress indicator
- [ ] Test test result display
- [ ] Test error detail view
- [ ] Test summary statistics

### test_help_panel.py
- [ ] Test shortcuts list display
- [ ] Test shortcuts search
- [ ] Test context-sensitive help

## Phase 4: Integration Tests

### test_integration.py
- [ ] Test full startup → navigate → shutdown workflow
- [ ] Test agent start → task assignment → monitoring → completion
- [ ] Test multi-panel navigation with state preservation
- [ ] Test concurrent agent updates while navigating
- [ ] Test error recovery scenarios
- [ ] Test terminal resize during operation
- [ ] Test theme switch during operation
- [ ] Test long-running session (memory leak check)

## Phase 5: Error Handling Tests

### test_error_handling.py
- [ ] Test agent crash doesn't crash UI
- [ ] Test file read error shows dialog
- [ ] Test file write error shows dialog
- [ ] Test disk full scenario
- [ ] Test permission denied scenario
- [ ] Test invalid JSON config handling
- [ ] Test network timeout handling
- [ ] Test terminal too small
- [ ] Test color init failure
- [ ] Test all uncaught exceptions logged

## Test Coverage Goals

- **Overall**: ≥90% coverage
- **Core modules**: 100% coverage
- **Panel modules**: ≥85% coverage
- **Utility modules**: ≥80% coverage

## Performance Benchmarks

All tests should verify:
- Input latency: <50ms
- Update latency: <100ms
- Render time: <50ms per frame
- Memory: <50MB for 1000 logs + 50 tasks
- Startup time: <1 second

## Test Execution Strategy

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=agent_control_panel --cov-report=html

# Run specific phase
pytest tests/test_ui_manager.py tests/test_theme_manager.py -v

# Run with benchmarks
pytest tests/ -v --benchmark-only
```
