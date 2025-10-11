# Model Thinking & Reasoning - Complete Visibility Guide

## 🎯 Overview

The agent now provides **100% visibility** into what the AI model is thinking and doing. Every decision, action, and reasoning step is captured and displayed in real-time.

---

## 🚀 Quick Start

### View Model Thinking in Real-Time:

1. **Launch the agent:**
   ```bash
   agent
   ```

2. **Navigate to Model Thinking:**
   - Press `5` (or navigate with ↑↓)
   - Press Enter

3. **Watch the AI think:**
   - See planning decisions
   - Watch code analysis
   - Monitor verification checks
   - Track model interactions

---

## 📋 What You'll See

### Event Types Captured:

#### 🔄 **Cycle Start**
```
16:42:01 🔄 Cycle Start [Cycle 1]
  Beginning cycle 1
    • max_cycles: 0
    • cooldown: 120
```

#### 💭 **Thinking / Reasoning**
```
16:42:03 💭 Thinking [Cycle 1]
  Analyzing code structure and identifying refactoring opportunities
    • files_analyzed: 15
    • complexity_score: high
```

#### 🎯 **Strategy / Planning**
```
16:42:05 🎯 Strategy [Cycle 1]
  Limiting scope to: authentication module
```

#### 🔨 **Actions**
```
16:42:10 🔨 Action [Cycle 1]
  run_analyze: Executing analyze command [started]

16:42:15 🔨 Action [Cycle 1]
  run_analyze: analyze command finished [completed]
```

#### 🤖 **Model Interactions**
```
16:42:20 🤖 Model Interaction [Cycle 1]
  → Prompt composed (15234 chars)
  ← Response received (4521 chars)
```

#### 📝 **Code Generation**
```
16:42:25 📝 Code Generation [Cycle 1]
  MODIFY: auth/login.py, auth/session.py (127 lines)
```

#### ⚡ **Decisions**
```
16:42:30 ⚡ Decision [Cycle 1]
  Extracted patch with changes
    • patch_size: 3842
```

#### ✅ **Verification**
```
16:42:35 ✅ Verification [Cycle 1]
  ruff: ✓ PASSED
    No style issues found

16:42:40 ✅ Verification [Cycle 1]
  pytest_cov: ✓ PASSED
    All tests passed, coverage 87%

16:42:45 ✅ Verification [Cycle 1]
  security_scan: ✗ FAILED
    2 high-severity issues found
```

#### 🔍 **Analysis**
```
16:42:50 🔍 Analysis [Cycle 1]
  Detected 3 changed files
    • files: ['auth/login.py', 'auth/session.py', 'tests/test_auth.py']
```

#### ❌ **Errors**
```
16:42:55 ❌ Error [Cycle 1]
  provider: Provider timeout after 120s
```

---

## 🎨 Visual Features

### Color Coding:
- **Green (✓)**: Successful operations, passed checks
- **Red (✗)**: Failures, errors
- **Cyan**: Event types, headings
- **Dim Gray**: Timestamps, metadata
- **Yellow/Blue**: Status indicators

### Timestamps:
Every event shows exact time (HH:MM:SS)

### Cycle Tracking:
See which cycle each event belongs to

### Structured Data:
Metadata displayed in organized format

---

## 🔧 Technical Details

### Storage Format

Events are stored in `agent/state/thinking.jsonl`:

```jsonl
{"timestamp": 1704567721.5, "cycle": 1, "event_type": "thinking", "data": {"type": "planning", "content": "Beginning cycle 1", "metadata": {}}}
{"timestamp": 1704567723.2, "cycle": 1, "event_type": "action", "data": {"action": "run_analyze", "details": "Executing analyze command", "status": "started"}}
```

### Event Schema

```python
{
    "timestamp": float,  # Unix timestamp
    "cycle": int | null,  # Cycle number
    "event_type": str,   # Event type
    "data": {            # Event-specific data
        # Varies by event_type
    }
}
```

### Event Types Reference

| Type | Icon | Description |
|------|------|-------------|
| `cycle_start` | 🔄 | New cycle begins |
| `thinking` | 💭 | General reasoning |
| `strategy` | 🎯 | Strategic planning |
| `action` | 🔨 | Operation performed |
| `analysis` | 🔍 | Code/data analysis |
| `decision` | ⚡ | Decision made |
| `model_interaction` | 🤖 | AI model called |
| `code_generation` | 📝 | Code modified |
| `verification` | ✅ | Quality check |
| `reflection` | 💭 | Self-assessment |
| `error` | ❌ | Failure occurred |

---

## 📊 Real-Time Updates

### Update Frequency:
- **TUI polls every 500ms**
- **Events appear instantly** as they're logged
- **Last 50 events** displayed (configurable)

### During Active Development:
Watch the agent think through:
1. **Planning Phase**: Strategy and scope decisions
2. **Analysis Phase**: Running linters, tests, security scans
3. **Generation Phase**: Composing prompts, getting AI responses
4. **Application Phase**: Applying patches, running gates
5. **Verification Phase**: Quality checks and results

---

## 🎯 Use Cases

### 1. Debugging Agent Behavior
```
Problem: Agent not modifying expected files
Solution: Check thinking log for:
  - Which files it detected
  - What scope it's using
  - What the model decided
  - Why certain files were excluded
```

### 2. Understanding AI Decisions
```
Question: Why did the agent refactor this way?
Answer: View thinking log for:
  - Strategy planning events
  - Analysis of code structure
  - Decision rationale
  - Alternative approaches considered
```

### 3. Monitoring Progress
```
Watch real-time:
  - Which cycle is running
  - Current phase (analyze/generate/verify)
  - Test results as they complete
  - Verification checks passing/failing
```

### 4. Identifying Performance Issues
```
Check thinking log for:
  - Long gaps between events
  - Slow model responses
  - Repeated failures
  - Timeout errors
```

---

## 🔍 Advanced Features

### Filter by Event Type

While the UI shows all events, you can programmatically filter:

```python
from agent.thinking_logger import ThinkingLogger
from pathlib import Path

logger = ThinkingLogger(Path("agent/state"))
events = logger.get_recent_events(
    limit=100,
    event_types=["verification", "error"]
)
```

### Get Events for Specific Cycle

```python
cycle_5_events = logger.get_cycle_events(cycle_num=5)
```

### Clear History

```python
logger.clear_history()
```

---

## 📈 Performance Considerations

### File Size Management:
- **JSONL format** allows incremental reading
- **Efficient parsing** only reads necessary lines
- **Automatic rotation** (future feature) at 10MB

### Memory Usage:
- **Streaming approach** doesn't load entire history
- **Fixed limit** of 100 events in memory
- **Minimal overhead** (<1% CPU impact)

---

## 🛠️ Configuration

### Change Event Limit

Edit `agent/tui/state_watcher.py`:

```python
def _read_thinking_events(self, limit: int = 100):
    # Change 100 to desired number
```

### Disable Thinking Logs

Add to `agent/config.json`:

```json
{
  "tui": {
    "show_thinking": false
  }
}
```

### Verbose Logging

Enable detailed logging in `agent/run.py`:

```python
self.thinking_logger.log_thinking(
    "reasoning",
    "Detailed analysis here",
    {"verbose": True, "details": {...}}
)
```

---

## 🐛 Troubleshooting

### No Events Appearing

**Check:**
1. Agent is actually running (not just TUI)
2. File exists: `agent/state/thinking.jsonl`
3. File has content: `cat agent/state/thinking.jsonl`
4. No JSON parse errors in logs

### Events Not Updating

**Check:**
1. TUI is polling: look for state updates
2. File permissions: can read `agent/state/`
3. Refresh rate: should update every 500ms

### Performance Issues

**Solutions:**
1. Reduce event limit (less than 100)
2. Clear old events: `rm agent/state/thinking.jsonl`
3. Reduce polling frequency in app.py

---

## 📚 API Reference

### ThinkingLogger Methods

```python
# Initialize
logger = ThinkingLogger(state_root: Path)

# Start cycle
logger.start_cycle(cycle_num: int)

# Log thinking
logger.log_thinking(
    thought_type: str,
    content: str,
    metadata: Optional[Dict] = None
)

# Log action
logger.log_action(
    action: str,
    details: str,
    status: str = "started"  # started, completed, failed
)

# Log decision
logger.log_decision(
    decision: str,
    rationale: str,
    alternatives: Optional[list] = None
)

# Log verification
logger.log_verification(
    check_name: str,
    passed: bool,
    message: str
)

# Log model interaction
logger.log_model_interaction(
    prompt_summary: str,
    response_summary: str,
    prompt_tokens: Optional[int] = None,
    response_tokens: Optional[int] = None
)

# Log code generation
logger.log_code_generation(
    file_path: str,
    operation: str,  # create, modify, delete
    lines_changed: int
)

# Log analysis
logger.log_analysis(
    subject: str,
    analysis: str,
    file_path: Optional[str] = None
)

# Log strategy
logger.log_strategy(
    strategy: str,
    steps: list,
    expected_outcome: str
)

# Log error
logger.log_error(
    error_type: str,
    message: str,
    details: Optional[Dict] = None
)
```

---

## 🎓 Best Practices

### 1. Meaningful Event Names
✅ Good: `logger.log_action("apply_patch", "Applying 15 file changes", "started")`
❌ Bad: `logger.log_action("action", "doing stuff", "ok")`

### 2. Include Context
✅ Good: `logger.log_thinking("analysis", "Found security issue", {"severity": "high", "file": "auth.py"})`
❌ Bad: `logger.log_thinking("thinking", "something happened")`

### 3. Log Both Start and End
```python
logger.log_action("run_tests", "Executing test suite", "started")
# ... run tests ...
logger.log_action("run_tests", f"Tests completed: {result}", "completed")
```

### 4. Capture Failures
```python
try:
    result = risky_operation()
except Exception as e:
    logger.log_error("operation_failed", str(e), {"stack": traceback})
```

---

## 🚀 Future Enhancements

Planned features:
- [ ] Event filtering in UI
- [ ] Search functionality
- [ ] Export to formats (JSON, CSV, HTML)
- [ ] Playback mode (step through events)
- [ ] Timeline visualization
- [ ] Performance analytics
- [ ] Comparison between cycles
- [ ] Alert rules (notify on errors)

---

## 🤝 Contributing

To add new event types:

1. Add to `ThinkingLogger` class
2. Update `icons` dict in `app.py`
3. Add display logic in `open_thinking_log()`
4. Update this documentation

---

**Now you have COMPLETE VISIBILITY into your AI agent! 🎉**

Every thought, decision, and action is captured and displayed in real-time.

Press `5` to start watching! 👀
