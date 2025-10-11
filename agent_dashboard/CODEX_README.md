# Codex-Style Dashboard

A modern, feature-rich TUI (Terminal User Interface) for monitoring and controlling the autonomous AI agent, inspired by OpenAI Codex.

## Features

### Modern Dark Theme
- Rich blacks and deep backgrounds (#0A0E27, #0D1117)
- Accent colors: cyan/blue highlights, green for success, yellow for warnings, red for errors
- Professional gradient effects and modern typography
- Smooth animations and responsive layout

### Real-Time Monitoring
- **AI Thinking Stream**: Live display of agent thoughts from `thinking.jsonl`
  - Event type indicators (CYCLE START, ACTION, THINKING, DECISION, etc.)
  - Color-coded status (started, completed, failed)
  - Syntax highlighting for code snippets
  - Auto-scroll with toggle option

- **Task Management**: Complete task lifecycle
  - Add new tasks with descriptions
  - Activate tasks to run them
  - Delete tasks no longer needed
  - View status: Pending, In Progress, Completed, Failed
  - Colored status badges

- **Log Viewer**: Comprehensive logging
  - Real-time log streaming
  - Log level filtering (ALL, INFO, WARN, ERROR)
  - Color-coded by severity
  - Auto-scroll with toggle
  - Clear logs functionality

- **Code Viewer**: Browse and view files
  - Directory tree navigation
  - Syntax highlighting for 30+ languages
  - Line numbers and indent guides
  - Quick filters (Agent files, All files)
  - Monokai theme for code display

### Live Metrics Sidebar
- Progress tracking (cycle count, percentage)
- Task statistics (pending, in progress, completed)
- System status (errors, warnings, mode)
- Current task display
- Real-time updates (100ms refresh rate)

### Status Header
- Model information
- Session ID
- Current cycle number
- Agent status with color indicators
- Elapsed time (HH:MM:SS format)

### Navigation & Controls
- Left sidebar with organized menu
- Quick access to all views
- Agent control buttons (Start, Pause, Stop, Verify)
- System options (Model config, Exit)

## Installation

### Dependencies

The Codex dashboard requires three additional Python packages:

```bash
pip install textual>=0.47.0 rich>=13.7.0 pygments>=2.17.0
```

Or install from the project root:

```bash
pip install -e .
```

### Verify Installation

```bash
python -c "import textual, rich, pygments; print('All dependencies installed!')"
```

## Usage

### Launch the Codex Dashboard

```bash
agent --codex
```

Or directly:

```bash
python -m agent_dashboard.codex_dashboard
```

### Keyboard Shortcuts

#### Navigation
- `1` - Show Tasks panel
- `2` - Show AI Thinking stream
- `3` - Show Logs
- `4` - Show Code viewer

#### Agent Controls
- `s` - Start agent
- `p` - Pause agent
- `x` - Stop agent
- `r` - Run verification tests

#### System
- `q` - Quit application
- `Ctrl+C` - Emergency exit

### Task Management

1. **Add a Task**
   - Type task description in the input field
   - Press Enter or click "Add Task"
   - Task appears in table with PENDING status

2. **Activate a Task**
   - Select task in table using arrow keys
   - Click "Activate" or press Enter
   - Task status changes to IN PROGRESS
   - Agent begins working on it

3. **Delete a Task**
   - Select task in table
   - Click "Delete" button
   - Task is removed from list

### AI Thinking Stream

The thinking stream displays real-time events from `agent/state/thinking.jsonl`:

- **Cycle Events**: CYCLE START, CYCLE END
- **Thinking**: Agent reasoning and analysis
- **Actions**: File operations, commands, patches
- **Decisions**: Strategy and planning choices
- **Verifications**: Test results and checks
- **Model Interactions**: API calls and responses
- **Code Generation**: Code snippets and patches

Each entry shows:
- Timestamp (HH:MM:SS)
- Cycle number (C001, C002, etc.)
- Event type (color-coded)
- Event details

### Log Viewer

Comprehensive logging with filtering:

- **All Levels**: Shows everything
- **Info**: General information only
- **Warning**: Warnings and above
- **Error**: Errors only

Controls:
- **Clear**: Remove all logs from display
- **Auto-scroll**: Toggle automatic scrolling (ON/OFF)

### Code Viewer

Browse and view project files:

1. **Navigate**: Use directory tree on left
2. **Select File**: Click to view with syntax highlighting
3. **Quick Filters**:
   - "Show Agent Files" - Only agent/ directory
   - "Show All Files" - Entire project
   - "Refresh Tree" - Reload directory structure

Supported languages: Python, JavaScript, TypeScript, JSON, YAML, Markdown, Shell, HTML, CSS, Rust, Go, Java, C/C++, Ruby, PHP, and more.

## Architecture

### Component Structure

```
agent_dashboard/
├── codex_dashboard.py          # Main application
├── codex_widgets/
│   ├── __init__.py
│   ├── status_header.py        # Top status bar
│   ├── nav_sidebar.py          # Left navigation
│   ├── metrics_sidebar.py      # Right metrics
│   ├── thinking_stream.py      # AI thoughts display
│   ├── task_panel.py           # Task management
│   ├── log_viewer.py           # Log display
│   └── code_viewer.py          # File browser
└── core/
    ├── real_agent_manager.py   # Agent integration
    └── models.py               # Data models
```

### Data Flow

1. **Agent Manager** (`RealAgentManager`)
   - Manages agent lifecycle
   - Reads from `thinking.jsonl`
   - Tracks tasks and state
   - Provides data to UI

2. **Main App** (`CodexDashboard`)
   - 100ms update loop
   - Distributes data to widgets
   - Handles user interactions
   - Manages panel switching

3. **Widgets**
   - Receive data updates
   - Format and display
   - Send events to main app
   - Self-contained rendering

### Theme Customization

Colors are defined in `theme_variables` in `codex_dashboard.py`:

```python
{
    "background": "#0A0E27",    # Deep blue-black
    "surface": "#0D1117",       # GitHub dark
    "panel": "#161B22",         # Panel background
    "boost": "#1F2937",         # Elevated elements
    "primary": "#30363D",       # Borders
    "accent": "#58A6FF",        # Blue highlights
    "success": "#3FB950",       # Green (success)
    "warning": "#D29922",       # Yellow (warnings)
    "error": "#F85149",         # Red (errors)
    "text": "#C9D1D9",          # Main text
    "text-muted": "#8B949E",    # Dimmed text
}
```

To customize, edit these values and restart the dashboard.

## Performance

### Update Rates
- **Main Loop**: 100ms (10 FPS)
- **Thinking Stream**: File polling every 100ms
- **State Updates**: Every cycle
- **UI Refresh**: On data change only

### Resource Usage
- Memory: ~50-100MB typical
- CPU: <5% idle, 10-20% active
- Disk I/O: Minimal (file tailing)

### Optimization Tips
- Increase update interval for slower systems
- Reduce log retention (maxlen in deque)
- Disable auto-scroll when viewing history
- Use filtered views instead of "All"

## Troubleshooting

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'textual'`

**Solution**: Install dependencies
```bash
pip install textual rich pygments
```

### Display Issues

**Error**: Terminal looks garbled or colors wrong

**Solution**: Ensure terminal supports 256 colors
```bash
echo $TERM  # Should be xterm-256color or similar
export TERM=xterm-256color
```

### File Not Found

**Error**: `thinking.jsonl not found`

**Solution**: Run agent first to generate files
```bash
agent  # Run agent normally first
```

Or create empty file:
```bash
mkdir -p agent/state
touch agent/state/thinking.jsonl
```

### Performance Issues

**Symptoms**: Slow updates, laggy UI

**Solutions**:
1. Increase update interval in `codex_dashboard.py`:
   ```python
   self._update_interval = 0.5  # 500ms instead of 100ms
   ```

2. Reduce deque sizes in `real_agent_manager.py`:
   ```python
   self.thoughts: deque = deque(maxlen=100)  # Instead of 1000
   self.logs: deque = deque(maxlen=500)      # Instead of 5000
   ```

3. Close other terminal applications

### Agent Not Starting

**Error**: Agent status stays IDLE

**Solution**: Check configuration
```bash
# Verify config exists
cat agent/config.json

# Check provider setup
agent --version
```

## Development

### Adding Custom Widgets

1. Create widget file in `codex_widgets/`:
```python
from textual.widget import Widget
from textual.app import ComposeResult

class MyWidget(Widget):
    def compose(self) -> ComposeResult:
        # Add your components
        pass
```

2. Add to `__init__.py`:
```python
from agent_dashboard.codex_widgets.my_widget import MyWidget
__all__ = [..., "MyWidget"]
```

3. Use in `codex_dashboard.py`:
```python
from agent_dashboard.codex_widgets import MyWidget

class CodexDashboard(App):
    def compose(self) -> ComposeResult:
        yield MyWidget()
```

### Customizing Event Formatting

Edit `_format_thinking_event()` in `thinking_stream.py` to change how events are displayed:

```python
def _format_thinking_event(self, event: dict) -> Text:
    # Your custom formatting logic
    text = Text()
    # Add custom styling
    return text
```

### Adding New Panels

1. Create widget for panel content
2. Add to `compose()` in `codex_dashboard.py`
3. Add navigation button in `nav_sidebar.py`
4. Add panel switching logic in `_show_panel()`

## FAQ

**Q: Can I use this with the old curses dashboard?**
A: Yes, use `agent --dashboard` for curses, `agent --codex` for new UI.

**Q: Does this work on Windows?**
A: Yes, but requires Windows Terminal or a compatible terminal emulator.

**Q: Can I run this remotely over SSH?**
A: Yes, works great over SSH with proper terminal support.

**Q: How do I export logs?**
A: Logs are stored in `~/.agent_cli/dashboard.log` automatically.

**Q: Can I customize colors?**
A: Yes, edit `theme_variables` in `codex_dashboard.py`.

**Q: Does this replace the agent?**
A: No, it's just a UI. The agent runs independently.

## License

Same as parent project.

## Contributing

Contributions welcome! Please ensure:
- Code follows existing style
- All features are fully implemented (no TODOs)
- Error handling is comprehensive
- Documentation is updated
- Tests pass (if applicable)

## Credits

Built with:
- [Textual](https://textual.textualize.io/) - Modern TUI framework
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal formatting
- [Pygments](https://pygments.org/) - Syntax highlighting

Inspired by OpenAI Codex interface design.
