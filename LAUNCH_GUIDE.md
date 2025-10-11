# 🚀 Quick Launch Guide

## Start the Dashboard

```bash
python3.11 -m agent_dashboard.__main__ --codex
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **1** or **T** | Tasks Panel |
| **2** or **A** | AI Thinking Stream |
| **3** or **L** | Logs Viewer |
| **4** or **C** | Code Viewer |
| **5** or **M** | Model Configuration ⭐ NEW! |
| **S** | Start Agent |
| **P** | Pause Agent |
| **X** | Stop Agent |
| **Q** | Quit Dashboard |

## Model Configuration (Press 5)

### Download Ollama Models
1. Press **5** to open Model Config
2. Select a model from the table
3. Click "Download Selected"
4. Wait for download to complete
5. Click "Use Selected" to activate

### Configure API Keys
1. Press **5** to open Model Config
2. Scroll to "API PROVIDERS" section
3. Select provider (OpenAI/Anthropic/Google)
4. Enter your API key
5. Click "Save API Config"

### Test Connection
1. Click "Test Connection" button
2. Verify provider is working
3. Check status message

## Current Setup

✓ Provider: **ollama**
✓ Model: **deepseek-coder:6.7b-instruct**
✓ Status: **Configured and ready**

## Quick Actions

**Add a Task:**
- Press 1 → Enter task → Click "Add Task"

**Watch AI Thinking:**
- Press 2 → See live thoughts from agent

**Start the Agent:**
- Press S → Agent begins autonomous operation

**Download Another Model:**
- Press 5 → Select model → "Download Selected"

## Files Created

- `agent/config.json` - Provider configuration
- `agent/local/api_keys.json` - API keys (if configured)
- `agent/state/thinking.jsonl` - AI thinking log
- `agent/local/control/task.txt` - Current task

## Everything Works!

All features are tested and functional:
- ✅ Model downloading
- ✅ API configuration
- ✅ Provider switching
- ✅ Connection testing
- ✅ Real-time updates
- ✅ Agent integration

**Ready to launch! 🎉**
