# Codex Dashboard - Quick Start Guide

## Installation (2 minutes)

### Option 1: Automatic (Recommended)
```bash
./install_codex.sh
```

### Option 2: Manual
```bash
pip install textual>=0.47.0 rich>=13.7.0 pygments>=2.17.0
```

### Option 3: From pyproject.toml
```bash
pip install -e .
```

## Launch

```bash
agent --codex
```

That's it! The dashboard will start immediately.

## First Time Setup (Optional)

If you want to see sample data for testing:

```bash
python3 agent_dashboard/codex_demo.py
agent --codex
```

## Quick Tour (30 seconds)

### Navigation (Number Keys)
- **1** = Tasks & Goals
- **2** = AI Thinking Stream (live events)
- **3** = Execution Logs
- **4** = Code Viewer

### Agent Controls (Letter Keys)
- **s** = Start agent
- **p** = Pause agent
- **x** = Stop agent
- **r** = Run verification tests
- **q** = Quit

### Layout Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│ MODEL: ollama:deepseek | SESSION: 123 | CYCLE: 5 | STATUS: RUNNING │ ← Status Header
├──────────┬──────────────────────────────────────────┬───────────────┤
│          │                                          │               │
│  Tasks   │                                          │   Progress    │
│  Thinking│         MAIN CONTENT AREA                │   Cycle: 5    │
│  Logs    │      (changes based on selection)        │   Tasks: 3    │
│  Code    │                                          │   Errors: 0   │
│          │                                          │               │
│  Start   │                                          │ Current Task  │
│  Pause   │                                          │ "Implement..."│
│  Stop    │                                          │               │
│  Verify  │                                          │               │
│          │                                          │               │
├──────────┴──────────────────────────────────────────┴───────────────┤
│ q Quit | 1 Tasks | 2 Thinking | 3 Logs | 4 Code | s Start | x Stop │ ← Footer
└─────────────────────────────────────────────────────────────────────┘
```

## Common Tasks

### Add a Task
1. Press **1** for Tasks panel
2. Type task description in input field
3. Press **Enter**

### Start Agent
1. Press **s** (or click "Start Agent" in sidebar)
2. Watch status change to "RUNNING" in header
3. See cycle counter increment

### Watch AI Thinking
1. Press **2** for Thinking Stream
2. Auto-scrolls as events appear
3. Color-coded by event type:
   - **Blue** = Actions
   - **Yellow** = Thinking
   - **Green** = Completions
   - **Cyan** = Decisions
   - **Red** = Errors

### View Logs
1. Press **3** for Logs
2. Use filter dropdown for specific levels
3. Toggle auto-scroll ON/OFF
4. Click "Clear" to reset

### Browse Code
1. Press **4** for Code Viewer
2. Click files in tree to view
3. Syntax highlighting automatic
4. Use "Show Agent Files" for quick filter

## Keyboard Shortcuts (All of Them)

### Navigation
| Key | Action |
|-----|--------|
| 1 | Show Tasks panel |
| 2 | Show AI Thinking stream |
| 3 | Show Logs |
| 4 | Show Code viewer |

### Agent Control
| Key | Action |
|-----|--------|
| s | Start agent |
| p | Pause agent |
| x | Stop agent |
| r | Run verification |

### System
| Key | Action |
|-----|--------|
| q | Quit application |
| Ctrl+C | Emergency exit |

### Within Panels
- **Arrow Keys**: Navigate tables/trees
- **Enter**: Activate selected item
- **Tab**: Move between UI elements
- **Space**: Toggle selections

## Tips & Tricks

### Performance
- Default refresh: 10 FPS (100ms)
- Low CPU usage: <5% idle
- Memory: ~50-100MB

### Viewing History
1. Turn off auto-scroll in logs/thinking
2. Scroll up to view old entries
3. Turn auto-scroll back on for live mode

### Multi-Monitor
- Works great over SSH
- Resize terminal anytime
- Layout adapts automatically

### Color Schemes
- Dark theme by default (Codex-inspired)
- Customizable in `codex_dashboard.py`
- Edit `theme_variables` dict

## Troubleshooting

### "ModuleNotFoundError: No module named 'textual'"
```bash
pip install textual rich pygments
```

### Terminal looks wrong
```bash
export TERM=xterm-256color
```

### Nothing happening
- Check agent status in header
- Press 's' to start agent
- Verify config file exists: `cat agent/config.json`

### Agent not found
```bash
pip install -e .  # Install from repo root
```

## Examples

### Example 1: Basic Usage
```bash
# Install
./install_codex.sh

# Launch
agent --codex

# Add task (in UI)
[Type]: "Fix bug in authentication module"
[Press]: Enter

# Start agent
[Press]: s

# Watch it work
[Press]: 2  # View thinking stream
```

### Example 2: Monitoring Running Agent
```bash
# Terminal 1: Run agent
agent

# Terminal 2: Watch with dashboard
agent --codex
[Press]: 2  # View thinking stream in real-time
```

### Example 3: Code Review
```bash
agent --codex
[Press]: 4  # Code viewer
[Click]: agent/run.py
[Read]: Syntax highlighted code
```

## What's Next?

- **Read full docs**: `agent_dashboard/CODEX_README.md`
- **Customize theme**: Edit `codex_dashboard.py`
- **Add custom widgets**: See CODEX_README.md "Development" section
- **Report issues**: Check repo issues page

## Need Help?

1. Check `CODEX_README.md` for detailed docs
2. Run demo: `python3 agent_dashboard/codex_demo.py`
3. View logs: `cat ~/.agent_cli/dashboard.log`
4. Open an issue on GitHub

## Comparison: Old vs New

| Feature | Curses (`--dashboard`) | Codex (`--codex`) |
|---------|------------------------|-------------------|
| Theme | Basic colors | Modern dark (Codex-inspired) |
| Thinking | Text display | Live stream with colors |
| Code view | Basic | Syntax highlighted |
| Updates | Manual refresh | Real-time (10 FPS) |
| Keyboard | Limited | Full shortcuts |
| Animations | None | Smooth transitions |
| Metrics | Basic stats | Live sidebar |

Both work great - choose based on preference!

## Summary

1. **Install**: `./install_codex.sh`
2. **Launch**: `agent --codex`
3. **Navigate**: Number keys (1-4)
4. **Control**: Letter keys (s/p/x/r)
5. **Quit**: Press q

That's all you need to know to get started!

Enjoy the Codex Dashboard! 🚀
