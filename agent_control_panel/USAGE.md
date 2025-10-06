# Usage Guide

## Installation

```bash
cd agent_control_panel
pip install -e .[dev]
```

## Quick Start

```bash
# Launch the control panel
python -m agent_control_panel

# Or use the installed command
agent-control
```

## First Launch

When you first launch, you'll see:

```
┌─ Agent Control Panel - Dashboard ─────────────────┐
│ Status: IDLE                                       │
│                                                    │
│ Model: gpt-4                                       │
│ Provider: openai                                   │
│ Cycle: 0/0                                         │
│ Duration: 0s                                       │
│                                                    │
│ Thoughts: 0                                        │
│ Actions: 0                                         │
└────────────────────────────────────────────────────┘
```

## Navigation

### Global Shortcuts

- `1` - Home Panel (Dashboard)
- `2` - Tasks Panel
- `3` - Thinking Panel (AI reasoning stream)
- `4` - Logs Panel
- `8` - Help Panel
- `ESC` - Go back to previous panel
- `Ctrl+Q` - Quit application
- `Ctrl+R` - Force screen refresh
- `Ctrl+T` - Toggle dark/light theme

### Panel-Specific

#### Tasks Panel (`2`)
- `↑↓` - Navigate task list
- `N` - Create new task
- `E` - Edit selected task
- `D` - Delete selected task
- `Enter` - View task details

#### Thinking Panel (`3`)
- `↑↓` - Scroll through thoughts
- `Home` - Jump to top
- `End` - Jump to bottom (re-enable auto-scroll)
- `Page Up/Down` - Scroll by page

#### Logs Panel (`4`)
- `↑↓` - Scroll through logs
- `F` - Toggle filter (errors only / all logs)
- `/` - Search logs
- `C` - Clear logs (with confirmation)
- `S` - Save logs to file

## Workflows

### Creating and Managing Tasks

1. Press `2` to open Tasks panel
2. Press `N` to create new task
3. Enter task description
4. Use `↑↓` to navigate
5. Press `E` to edit
6. Press `D` to delete

### Monitoring Agent Execution

1. Start your agent (outside this UI)
2. Press `3` for live thinking stream
3. Press `4` for execution logs
4. Press `1` to see dashboard metrics

### Debugging Issues

1. Press `4` for logs
2. Press `F` to filter errors only
3. Navigate to specific error
4. Check thinking stream (`3`) for context
5. Review agent status in header

## Configuration

### Theme Preference

Saved automatically to `~/.agent_cli/theme.json`

```json
{
  "theme": "dark"
}
```

Toggle with `Ctrl+T` in the UI.

### State Persistence

All panel states saved to `~/.agent_cli/state.json`:

```json
{
  "tasks.scroll_offset": 5,
  "logs.filter_level": "error",
  "thinking.auto_scroll": true
}
```

### Logs

Application logs at `~/.agent_cli/control_panel.log`

```bash
# View logs
tail -f ~/.agent_cli/control_panel.log

# Search logs
grep ERROR ~/.agent_cli/control_panel.log
```

## Terminal Requirements

### Minimum Size
- **80 columns × 24 rows**

### Recommended Size
- **120 columns × 40 rows** or larger

### Supported Terminals

✅ Tested and working:
- iTerm2 (macOS)
- Terminal.app (macOS)
- GNOME Terminal (Linux)
- Konsole (Linux)
- Windows Terminal

⚠️ Limited support:
- tmux (colors may be limited)
- screen (no 256 colors)

❌ Not supported:
- Terminals < 80x24
- Non-ANSI terminals

## Troubleshooting

### "Terminal too small" Error

```
Error: Terminal too small (min 80x24)
```

**Solution:** Resize your terminal window

```bash
# Check current size
echo $LINES $COLUMNS

# Most terminals: Cmd/Ctrl + Plus to increase size
```

### UI Not Responding

**Symptoms:** Keys don't work, screen frozen

**Solutions:**
1. Press `Ctrl+R` to force refresh
2. Press `Ctrl+Q` to quit and restart
3. Check logs: `~/.agent_cli/control_panel.log`

### Colors Not Working

**Symptoms:** Everything is black and white

**Cause:** Terminal doesn't support colors

**Solutions:**
1. Use a modern terminal (iTerm2, GNOME Terminal)
2. Check `$TERM` variable
3. UI will automatically fall back to monochrome

### Agent Not Connecting

**Symptoms:** Status shows "IDLE", no thoughts/logs

**Cause:** Agent process not running

**Solutions:**
1. Start your agent process separately
2. Check agent is running on expected port
3. Review agent connection settings

### Crashes or Errors

```
Fatal error: [error message]
```

**Recovery:**
1. Check `~/.agent_cli/control_panel.log`
2. Remove corrupted state: `rm ~/.agent_cli/state.json`
3. Report issue with log file

## Performance Tips

### Large Task Lists

- Use pagination (auto-enabled > 50 tasks)
- Search/filter instead of scrolling
- Archive completed tasks periodically

### Many Logs

- Use filter (`F`) to show errors only
- Clear old logs (`C`) periodically
- Logs auto-limit to 5000 entries

### Slow Rendering

- Reduce terminal size if too large (>200 columns)
- Check system CPU usage
- Disable auto-scroll in thinking panel

## Advanced Usage

### Custom Panel Layout

Edit `~/.agent_cli/layout.json`:

```json
{
  "sidebar_width": 25,
  "header_height": 3,
  "footer_height": 2
}
```

### Keyboard Remapping

Edit `~/.agent_cli/keys.json`:

```json
{
  "panel_1": "h",
  "panel_2": "t",
  "quit": "q"
}
```

### Integration with Other Tools

```bash
# Watch agent status
watch -n 1 "jq .state ~/.agent_cli/state.json"

# Export logs
tail -100 ~/.agent_cli/control_panel.log > agent_logs.txt

# Monitor thoughts
tail -f ~/.agent_cli/thoughts.jsonl
```

## Best Practices

### Daily Workflow

1. Launch control panel: `python -m agent_control_panel`
2. Create tasks for the day (`2` → `N`)
3. Start agent process
4. Monitor thinking stream (`3`)
5. Check logs for errors (`4` → `F`)
6. Review completed tasks (`2`)

### Debugging Workflow

1. Reproduce issue
2. Check logs (`4`) for errors
3. Review thinking stream (`3`) for context
4. Check agent status (header)
5. Save logs (`S`) for reporting

### Performance Workflow

1. Monitor metrics (dashboard `1`)
2. Check thought rate (thinking panel `3`)
3. Review action count (sidebar)
4. Identify bottlenecks in logs (`4`)

## FAQ

**Q: Can I run multiple instances?**
A: No, state file will conflict. Use different `--state-dir` flags.

**Q: How do I change the model?**
A: Use Model Config panel (panel 6, not yet implemented in this version)

**Q: Can I export my tasks?**
A: Yes, tasks stored in `~/.agent_cli/state.json` as JSON

**Q: Is there a headless mode?**
A: No, this is a TUI. Use the agent's CLI for headless operation.

**Q: Can I customize colors?**
A: Theme customization coming in v1.1. Currently dark/light only.

## Getting Help

1. Press `8` in the UI for keyboard shortcuts
2. Read `ARCHITECTURE.md` for technical details
3. Read `TESTING.md` for contributing
4. Check logs at `~/.agent_cli/control_panel.log`
5. File issue at project repository

## Keyboard Shortcuts Reference

### Global
| Key | Action |
|-----|--------|
| 1-9 | Switch to panel |
| ESC | Go back |
| Ctrl+Q | Quit |
| Ctrl+R | Refresh |
| Ctrl+T | Toggle theme |

### Tasks Panel
| Key | Action |
|-----|--------|
| ↑↓ | Navigate |
| N | New task |
| E | Edit |
| D | Delete |
| Enter | Details |

### Thinking Panel
| Key | Action |
|-----|--------|
| ↑↓ | Scroll |
| Home | Top |
| End | Bottom (auto-scroll) |
| PgUp/Dn | Page scroll |

### Logs Panel
| Key | Action |
|-----|--------|
| ↑↓ | Scroll |
| F | Filter errors |
| / | Search |
| C | Clear |
| S | Save |
