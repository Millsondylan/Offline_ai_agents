# Testing Guide

## Quick Start

To launch the agent TUI with all new features:

```bash
agent
# or
python3 -m agent.tui.main
```

## Testing New Features

### 1. Test Task Manager
1. Launch the agent: `agent`
2. Press `4` or navigate to "Task Manager"
3. Press Enter
4. You should see the Task Manager detail view with information about creating execution tasks

### 2. Test Model Thinking Log
1. In the main menu, press `5` or navigate to "Model Thinking"
2. Press Enter
3. You should see the Model Thinking Log detail view explaining the thinking process viewer

### 3. Test Model Configuration
1. Press `6` or navigate to "Model Config"
2. Press Enter
3. View current model and available models
4. See API key configuration options

### 4. Test Verification Configuration
1. Press `7` or navigate to "Verification"
2. Press Enter
3. See all verification checks organized by priority level
4. View configuration options

### 5. Test Navigation
- Use **1-9, 0** to jump to menu items
- Use **↑/↓** or **j/k** (vim style) to navigate
- Use **Enter** or **Space** to activate
- Use **ESC** or **q** to quit/go back

## Feature Verification Checklist

- [ ] Agent launches without errors
- [ ] All 10+ menu items are visible
- [ ] Can navigate with number keys
- [ ] Can navigate with arrow keys
- [ ] Task Manager opens detail view
- [ ] Model Thinking opens detail view
- [ ] Model Config shows available models
- [ ] Verification Config shows all checks
- [ ] Status bar shows actions
- [ ] Can return to menu with ESC

## Common Issues

### AttributeError on Launch
**Fixed!** If you see `AttributeError: can't set attribute`, it was related to RichLog initialization. This has been resolved in commit 2f71c64.

### Command Not Found: agent
Install the agent locally:
```bash
pip3 install -e .
```

### Import Errors
Ensure all dependencies are installed:
```bash
pip3 install textual rich
```

## Advanced Testing

### Test Task Execution
To actually create and run a task (requires full agent setup):
1. Ensure test data is generated
2. Navigate to Task Manager
3. Note: Full task execution requires the agent loop to be running

### Test Model Switching
To test model switching:
1. Ensure Ollama is installed and running (for offline models)
2. Or have API keys configured (for cloud models)
3. Use the Model Config menu to switch

### Test Verification Checks
To run actual verification:
1. Create a task
2. Watch as it runs through all enabled checks
3. View detailed results in task details

## Performance Testing

Monitor performance:
- Memory usage should be stable
- UI should remain responsive
- Navigation should be instant
- Status updates should be real-time (within 0.5s)

## Debugging

Enable debug mode:
```bash
TEXTUAL_DEBUG=1 agent
```

View logs:
```bash
tail -f agent/local/agent.log
```

## Success Criteria

✅ Agent launches without errors
✅ All new menu items appear
✅ Navigation works smoothly
✅ Detail views display correctly
✅ No Python exceptions in terminal
✅ UI is responsive and fast

## Next Steps After Testing

Once basic testing passes:
1. Test with actual agent loop running
2. Create real execution tasks
3. Monitor AI thinking in real-time
4. Configure verification settings
5. Switch between models
6. Run full verification suite

## Reporting Issues

If you find bugs:
1. Note the exact steps to reproduce
2. Check the terminal for error messages
3. Look for Python tracebacks
4. Create an issue with details

Happy testing! 🚀
