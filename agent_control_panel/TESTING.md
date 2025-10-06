# Testing Guide

## Test-Driven Development Process

This project follows **strict TDD**:

1. ✅ Write tests first
2. ✅ Run tests (they fail)
3. ✅ Implement minimum code to pass
4. ✅ Refactor for quality
5. ✅ Verify all tests pass

**No code is complete until all tests pass.**

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_ui_manager.py -v

# With coverage
pytest tests/ --cov=agent_control_panel --cov-report=html

# Parallel execution
pytest tests/ -n auto

# Only fast tests (skip integration)
pytest tests/ -m "not integration"
```

## Test Organization

### Phase 1: Core UI Framework
- `test_theme_manager.py` - Theme switching, colors, persistence
- `test_keyboard.py` - Key mapping, sequences, edge cases
- `test_layout.py` - Screen calculations, resize handling
- `test_base_panel.py` - Panel lifecycle, scrolling, state
- `test_ui_manager.py` - Main controller, rendering, navigation

### Phase 2: Agent Integration
- `test_agent_controller.py` - Agent control, messaging, recovery
- `test_state_manager.py` - Persistence, undo/redo, concurrency

### Phase 3: Panels
- `test_home_panel.py` - Dashboard rendering
- `test_task_panel.py` - Task CRUD operations
- `test_thinking_panel.py` - Thought streaming
- `test_logs_panel.py` - Log filtering, search
- `test_help_panel.py` - Help display

### Phase 4: Integration
- `test_integration.py` - Full workflows, state preservation

### Phase 5: Error Handling
- `test_error_handling.py` - Crash scenarios, recovery

## Test Fixtures

### `conftest.py` Provides:

- `mock_stdscr` - Mock curses window
- `sample_agent_status` - Pre-populated agent status
- `sample_tasks` - List of test tasks
- `sample_thoughts` - Deque of thoughts
- `sample_logs` - Deque of log entries
- `sample_model_config` - Model configuration
- `mock_agent_controller` - Mock agent controller
- `mock_state_manager` - Mock state manager

## Coverage Goals

| Component | Target | Actual |
|-----------|--------|--------|
| Core modules | 100% | TBD |
| Panel modules | 85% | TBD |
| Utility modules | 90% | TBD |
| **Overall** | **90%** | **TBD** |

## Writing New Tests

### Unit Test Template

```python
"""Tests for NewComponent."""

import pytest


class TestNewComponent:
    """Test new component functionality."""

    def test_happy_path(self):
        """Test normal operation."""
        from agent_control_panel.module import NewComponent

        component = NewComponent()
        result = component.do_something()

        assert result == expected_value

    def test_edge_case(self):
        """Test boundary condition."""
        component = NewComponent()

        # Test edge case
        result = component.handle_edge_case()

        assert result is handled_correctly

    def test_error_handling(self):
        """Test error recovery."""
        component = NewComponent()

        # Should not crash
        component.handle_error()

        assert component.state == recovered
```

### Integration Test Template

```python
"""Integration tests."""

import pytest


@pytest.mark.integration
class TestFullWorkflow:
    """Test complete user workflows."""

    def test_task_creation_workflow(self, mock_stdscr):
        """Test creating and managing a task."""
        # Setup
        ui = UIManager(mock_stdscr, agent_controller)

        # Navigate to tasks
        ui.switch_panel("tasks")

        # Create task
        ui.handle_key_code(ord('n'))

        # Verify
        assert len(task_panel.tasks) == 1
```

## Mocking Strategy

### Curses Mocking

```python
@pytest.fixture
def mock_stdscr():
    screen = MagicMock()
    screen.getmaxyx.return_value = (24, 80)
    screen.getch.return_value = -1
    return screen
```

### Agent Mocking

```python
@pytest.fixture
def mock_agent_controller():
    controller = Mock()
    controller.get_status.return_value = AgentStatus(...)
    controller.subscribe_thoughts.return_value = None
    return controller
```

## Performance Testing

### Render Performance

```python
def test_render_performance(mock_stdscr):
    """Test render completes within 50ms."""
    ui = UIManager(mock_stdscr, agent_controller)

    import time
    start = time.perf_counter()
    ui.render()
    duration_ms = (time.perf_counter() - start) * 1000

    assert duration_ms < 50
```

### Memory Testing

```python
def test_memory_bounds(agent_controller):
    """Test queues don't exceed max size."""
    # Add more than max
    for i in range(2000):
        agent_controller._emit_thought(Mock())

    thoughts = agent_controller.get_pending_thoughts()
    assert len(thoughts) <= 1000
```

## Thread Safety Testing

```python
def test_concurrent_access():
    """Test thread-safe operations."""
    manager = StateManager()
    errors = []

    def writer():
        try:
            for i in range(100):
                manager.set(f"key_{i}", i)
        except Exception as e:
            errors.append(e)

    threads = [Thread(target=writer) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e .[dev]
      - run: pytest tests/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Debugging Failed Tests

### Verbose Output

```bash
pytest tests/test_failing.py -vv --tb=long
```

### PDB on Failure

```bash
pytest tests/test_failing.py --pdb
```

### Capture Logging

```bash
pytest tests/test_failing.py -v --log-cli-level=DEBUG
```

## Test Quality Checklist

- [ ] Test name clearly describes what is tested
- [ ] Test is deterministic (no random values)
- [ ] Test is isolated (no shared state)
- [ ] Test is focused (one assertion per test)
- [ ] Test has clear AAA structure (Arrange, Act, Assert)
- [ ] Edge cases are covered
- [ ] Error conditions are tested
- [ ] Performance bounds are verified
- [ ] Thread safety is validated (if applicable)

## Common Patterns

### Testing Panel Rendering

```python
def test_panel_renders_content(mock_stdscr):
    panel = MyPanel(mock_stdscr)
    panel.render()

    # Verify addstr was called with expected content
    calls = [str(call) for call in mock_stdscr.addstr.call_args_list]
    assert any("expected text" in call for call in calls)
```

### Testing State Persistence

```python
def test_state_persists(tmp_path):
    state_file = tmp_path / "state.json"

    manager1 = StateManager(state_file)
    manager1.set("key", "value")
    manager1.save()

    manager2 = StateManager(state_file)
    assert manager2.get("key") == "value"
```

### Testing Error Recovery

```python
def test_recovers_from_error():
    component = Component()

    # Cause error
    component.cause_error()

    # Verify recovery
    component.recover()
    assert component.state == State.NORMAL
```

## Maintenance

### Adding Tests for New Features

1. Create test file: `tests/test_new_feature.py`
2. Write tests covering happy path, edge cases, errors
3. Run tests: `pytest tests/test_new_feature.py -v`
4. Implement feature to pass tests
5. Verify coverage: `pytest --cov=agent_control_panel.new_feature`

### Updating Tests After Refactoring

1. Run full suite: `pytest tests/ -v`
2. Fix broken tests
3. Verify coverage didn't decrease
4. Update test documentation if needed
