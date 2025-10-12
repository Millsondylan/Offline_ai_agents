# Offline Agent CLI

Always-on, offline-first AI agent for your local repositories. Ships with a minimal TUI and a headless loop that analyzes, proposes diffs, gates them with static analysis and tests, and optionally commits.

Works fully offline with local models via Ollama or with a manual provider. Designed for developers who want continuous, automated improvements without sending code to external services.

## Why This Agent

- Offline-first: use local LLMs via Ollama or manual review flows
- Always-on: background loop watches, proposes, gates, and applies patches
- Safe by default: gated by ruff, pytest+coverage, bandit, semgrep, pip-audit
- Git-native: applies unified diffs, creates isolated commits and optional branch
- TUI + headless: lightweight terminal UI plus scriptable CLI
- Clear artifacts: every cycle produces a browsable audit trail

## Installation

### Local virtualenv (recommended)

1. Install Python 3.11+ (macOS example):
   ```bash
   brew install python@3.12
   ```
2. Create and activate an isolated environment in this repo:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install the runtime dependencies:
   ```bash
   pip install textual watchdog requests keyring
   ```
4. (Optional) Install the production gate toolchain:
   ```bash
   pip install ruff bandit semgrep pip-audit pytest coverage
   ```

### Put the CLI on your PATH
```bash
export PATH="$PWD/scripts:$PATH"
```
Now `agent` will resolve to the repository launcher instead of any system/brew install. Re-run the export inside new shells or add it to your shell profile.

### Packaging options

- **Homebrew service (macOS):**
  ```bash
  brew tap Millsondylan/agent
  brew install agent
  brew services start agent
  ```
- **npm installer (macOS/Linux):**
  ```bash
  npm install -g @millsondylan/agent   # or: npx @millsondylan/agent -- --version
  ```
  The installer downloads a prebuilt binary when it exists and falls back to the Python module otherwise.
- **Direct download:**
  Download the latest release from [GitHub Releases](https://github.com/Millsondylan/Offline_ai_agents/releases)

### Requirements recap

- Python 3.11+ and `git`
- [Ollama](https://ollama.com/) (optional) for local models
- Optional tools for quality gates: `ruff`, `pytest`, `coverage`, `bandit`, `semgrep`, `pip-audit`

## Getting Started

Activate your virtualenv first: `source .venv/bin/activate`.

### Launch the TUI (Terminal User Interface)
```bash
agent
```

The TUI provides a complete real-time dashboard for monitoring and controlling the agent:

#### Navigation
- **↑/↓ Arrow Keys**: Navigate between all interactive elements (wraps around)
- **ENTER**: Execute focused action instantly (no confirmation dialogs)
- **ESC**: Exit TUI

#### TUI Features

**Control Panel**
- Live status indicator: ● RUNNING, ⏸ PAUSED, ⏹ STOPPED
- Pause/Resume agent execution
- Stop agent gracefully
- Force immediate commit
- Switch between available models (cycles through list)
- Session duration and cycle counter

**Task Queue**
- View all queued tasks with real-time status updates
- Add new tasks via inline input ([+ New Task] button)
- Status indicators: ▶ running, □ pending, ✓ complete, ✗ failed
- Automatically scrolls to keep focused task visible

**Gate Status & Safety**
- Real-time monitoring of all production gates
- Status indicators: ✓ passed, ✗ failed, ⟳ running, ⏳ pending
- View detailed findings for any gate (press ENTER)
- Monitors: Ruff, Bandit, Pytest, Mypy, Semgrep, and custom gates

**Artifact Browser**
- Navigate all generated files by cycle
- Hierarchical file tree (cycle_NNN/file.ext)
- Quick access to diffs, findings, logs, and config
- Press ENTER to open artifact in viewer

**Output Viewer** (Tabbed)
- **Diff Tab**: Syntax-highlighted diffs with apply/reject actions
- **Findings Tab**: Filtered findings by gate with severity levels
- **Logs Tab**: Auto-scrolling logs (last 100 lines)
- **Config Tab**: Interactive JSON editor (press ENTER to edit values inline)

#### Requirements
- Python 3.11+
- Textual framework (installed automatically via `pip install textual`)
- Terminal with minimum 80x24 size
- UTF-8 encoding for proper icons

If Textual is missing you will be prompted—install it with `pip install textual`.

### Run a bounded headless cycle
```bash
agent run --max-cycles=1
```

### Keep the agent running 24/7
- Local shell: `agent --headless --cooldown-seconds=0 &`
- macOS service: `brew services start agent`
- Linux sample: see `packaging/homebrew/README.md` for the systemd unit

### Timeboxed reviews and scheduled commits
```bash
agent review ./frontend --duration 45m --post-review 120m
agent commit --now            # force an immediate commit if gates pass
agent commit --cadence 900    # change scheduled cadence to 15 minutes
agent commit --off            # pause auto-commits
```

### Provider helpers
```bash
agent exec "Explain failing tests in cycle logs"
agent models                 # list available models
agent models --pull llama3   # download via Ollama
agent models --switch llama3 # select a default Ollama model
agent apikey set openai sk-...   # store hosted API keys securely
```

## How It Works

1) Analyze/Test: runs configured commands (analyze, test, e2e, screenshots) and captures logs
2) Compose Prompt: builds a prompt with git status, logs, and heuristically-relevant files
3) Provider: sends prompt to a provider (Ollama or Manual) and expects a unified diff
4) Patch Apply: applies the diff with `git apply` and records output
5) Gating: runs analyzers (ruff, pytest+coverage, bandit, semgrep, pip-audit, hygiene)
6) Commit/Push: optionally commits to a branch and can push (disabled by default)
7) Cooldown: sleeps between cycles; repeats while enabled

Artifacts per cycle are written to `agent/artifacts/cycle_<N>_<timestamp>` and include:
- `prompt.md`, provider outputs, and `proposed.patch`
- `apply_patch.log`, `production_gate.json`
- Analyzer reports: `ruff.json`, `pytest_cov.json`, `bandit.json`, `semgrep.json`, `pip_audit.json`, `repo_hygiene.json`
- Commit/push metadata when enabled

## Providers

This agent supports multiple AI providers (configured in `agent/config.json`):

### Local/Offline
- **Ollama** - Run models locally (recommended). Supports both HTTP API and CLI modes.
  - `deepseek-coder:6.7b-instruct` - Recommended coding model (~4GB)
  - `llama3`, `codellama`, etc.
  - Free, offline, no API keys needed

### Cloud APIs
- **OpenAI** - GPT-4, GPT-4o-mini, etc.
- **Anthropic** - Claude 3.5 Sonnet, Claude 3 Opus, etc.
- **Google Gemini** - Gemini 2.0 Flash, Gemini Pro

### Other
- **Manual** - Write patches manually for review

**📖 See [PROVIDER_SETUP.md](PROVIDER_SETUP.md) for complete setup instructions**

Quick start:
```bash
# Option 1: Local (Ollama)
brew install ollama
ollama serve
ollama pull deepseek-coder:6.7b-instruct

# Option 2: Cloud (OpenAI)
export OPENAI_API_KEY="sk-..."
```

Test your connection:
```bash
python3 test_provider_connection.py
```

## Configuration

Edit `agent/config.json` to fit your repo and workflows. Key fields:

- `provider.type`: `command` (default) or `manual`
- `provider.command.cmd`: shell array to invoke (e.g., run an Ollama model)
- `loop.max_cycles`: 0 for infinite; integer for a bounded run
- `loop.cooldown_seconds`: sleep between cycles
- `loop.apply_patches`: apply provider diffs automatically when present
- `loop.require_manual_approval`: when true, require `approve.txt` with `ok` in the cycle directory before applying
- `commands.*`: define `analyze`, `test`, `e2e`, and `screenshots` commands and timeouts
  - `screenshots.collect_glob`: copies matching files into artifacts for review
- `git.commit`: enable commit creation
- `git.branch`: working branch for commits (e.g., `agent/auto`)
- `git.push`: optional push to `git.remote` after commit
- `patch.path_prefix`: rewrite diff paths when your project lives under a subdir
- `gate.min_coverage`: minimum overall coverage threshold (if pytest/coverage tools available)
- `gate.semgrep_rules`: semgrep rule packs (e.g., `p/ci`, `p/python`)

Example (excerpt):

```json
{
  "provider": {
    "type": "command",
    "command": {"cmd": ["bash", "-lc", "bash agent/local/ollama_provider.sh"], "timeout_seconds": 1200}
  },
  "loop": {"max_cycles": 0, "cooldown_seconds": 30, "apply_patches": true, "require_manual_approval": false},
  "git": {"commit": true, "branch": "agent/auto", "push": false},
  "patch": {"path_prefix": "<optional-subdir>/"}
}
```

## Expected Provider Output

The agent extracts a unified diff from the provider response. Preferred format:

```diff
diff --git a/path/to/file.py b/path/to/file.py
--- a/path/to/file.py
+++ b/path/to/file.py
@@
-old
+new
```

Fenced blocks labeled `diff` or `patch` are supported. Raw `diff --git` streams also work. Non-diff text is ignored.

For local testing, `agent/local/echo_patch.sh` emits a sample diff.

## CLI Reference

- Default (TUI): `agent`
- Headless loop: `agent --headless [--cooldown-seconds N]`
- One-shot headless: `agent run --max-cycles=1`
- Timeboxed session: `agent review <scope> --duration 45m --post-review 120m`
- Commit scheduler controls: `agent commit --now`, `agent commit --cadence 900`, `agent commit --off`
- Provider exec: `agent exec "<prompt>"`
- Model management (Ollama or other local providers): `agent models`, `agent models --switch llama3`
- API keys: `agent apikey set openai sk-...`, `agent apikey clear openai`

## Tips & Troubleshooting

- Using macOS system Python 3.9? Create `.venv` with Homebrew’s 3.12 to avoid LibreSSL/urllib3 warnings.
- TUI missing? Install Textual (inside your env): `pip install textual`
- Patch fails to apply? Set `patch.path_prefix` when your project is nested.
- Missing tools? Install as needed:
  - `pip install ruff bandit semgrep pip-audit pytest coverage`
- Using Ollama? Ensure the model is present: `ollama pull llama3` (or your preferred model).

## Contributing

Contributions welcome! See `CONTRIBUTING.md` for guidelines. Please keep changes minimal, ensure analyzers/gates pass locally, and prioritize offline-first operation.

---

Built with care for offline workflows and transparent automation.
