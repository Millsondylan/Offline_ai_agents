# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-10-06

### Added
- **Complete TUI Interface**: Full-featured terminal UI with arrow-key navigation
  - Navigate entire interface using only UP/DOWN arrows with wrap-around
  - Auto-execution: All commands execute immediately on ENTER (no confirmations)
  - Live updates: Real-time state polling every 500ms
  - Focus preservation: Navigation state maintained during updates
  - Auto-scroll: Focused elements stay visible in long lists

- **Control Panel**
  - Pause/Resume/Stop/Force Commit buttons with instant execution
  - Live session status indicator (● RUNNING, ⏸ PAUSED, ⏹ STOPPED)
  - Provider and model display
  - Session duration and cycle counter

- **Task Queue Management**
  - View all queued tasks with status indicators (▶ running, □ pending, ✓ complete, ✗ failed)
  - Add new tasks via inline input
  - Toggle task status with ENTER
  - Scrollable list for 50+ tasks

- **Gate Status Monitoring**
  - Live monitoring of Ruff, Bandit, Pytest, Mypy, and custom gates
  - Visual indicators (✓ passed, ✗ failed, ⟳ running, ⏳ pending)
  - Click to view detailed findings
  - Scrollable panel for 20+ gates

- **Artifact Browser**
  - Navigate diffs, findings, logs, and config files
  - Hierarchical file tree by cycle
  - Quick access to all generated artifacts
  - Scrollable browser for 50+ files

- **Output Viewer**
  - Tabbed interface for diffs, findings, logs, and config
  - Syntax-highlighted diff viewer with apply/reject actions
  - Findings viewer with gate filtering
  - Auto-scrolling log viewer (last 100 lines)
  - Interactive config editor (edit values inline)

- **Model Switcher**
  - Cycle through available models with ENTER
  - Instant model switching via .cmd files
  - Display current model in control panel

- **Comprehensive Test Suite**
  - 30+ automated tests covering navigation, commands, state, and edge cases
  - Test data generator for stress testing with 60+ tasks, 20+ gates, 40+ artifacts
  - Edge case handling (empty state, corrupted JSON, missing directories)

### Changed
- Improved agent control via command (.cmd) files for zero-friction execution
- Enhanced state persistence with focus preservation during updates
- Better artifact organization with cycle-based hierarchy
- Upgraded navigation system with CSS-based focus (no conflicts with Textual focus)

### Fixed
- Focus stability during state updates (every 500ms)
- Scrolling issues in long lists (tasks, gates, artifacts)
- Terminal resize handling
- Widget focus preservation when rebuilding navigation chain

### Technical
- Built with Textual framework for high-performance terminal UI
- 500ms state polling interval for responsive updates
- Zero-confirmation auto-execution for all commands
- VerticalScroll containers with auto-scroll-to-focused
- CSS-based navigation with .focused class styling

## [0.2.17] - 2025-10-05

### Fixed
- Keyboard navigation in TUI
- Widget focus capture issues

## [0.2.16] - 2025-10-05

### Added
- Initial TUI implementation with basic navigation

## [0.2.0] - 2025-09-30

### Added
- Initial release with headless agent loop
- Production gates (Ruff, Bandit, Pytest, Coverage)
- Ollama provider support
- Git integration with auto-commit
- Command-based provider system

[0.3.0]: https://github.com/Millsondylan/Offline_ai_agents/compare/v0.2.17...v0.3.0
[0.2.17]: https://github.com/Millsondylan/Offline_ai_agents/compare/v0.2.16...v0.2.17
[0.2.16]: https://github.com/Millsondylan/Offline_ai_agents/compare/v0.2.0...v0.2.16
[0.2.0]: https://github.com/Millsondylan/Offline_ai_agents/releases/tag/v0.2.0
