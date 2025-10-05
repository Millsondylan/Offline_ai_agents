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

### Quick (no install)

- Run directly from this repo by adding `scripts` to your `PATH`:

  - `export PATH="$PWD/scripts:$PATH"; agent`

### Optional: Homebrew (experimental)

- This repo includes a Homebrew formula scaffold under `packaging/homebrew/`.
- To publish, update `homepage`, `url`, and `sha256` in `packaging/homebrew/agent.rb`, then host a tap and install:

  - `brew tap YOURORG/agent && brew install agent`

### Requirements

- Python 3.10+ and `git`
- Optional for TUI: `pip install textual`
- Optional for local LLMs: [Ollama](https://ollama.com/) with one or more models pulled
- Optional for gating: `ruff`, `pytest`, `coverage`, `bandit`, `semgrep`, `pip-audit`

## Getting Started

### Launch TUI

- `export PATH="$PWD/scripts:$PATH"; agent`

### Run headless (single cycle)

- `scripts/agent run --max-cycles=1`

### Run continuously in background

- Start: `scripts/agent-start`
- Stop: `scripts/agent-stop`
- Forever loop helper: `scripts/run_agent_forever.sh`

### Non-interactive prompt to provider

- `scripts/agent exec "Write a minimal patch adding a README section"`
  - Saves raw provider output under `agent/local/qa/<timestamp>/provider_output.txt`

### Ollama models helper

- List models: `scripts/agent models`
- Pull model: `scripts/agent models --pull qwen2.5-coder:7b-instruct`

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

This agent supports two provider modes (configured in `agent/config.json`):

- CommandProvider (default): pipes the prompt to a shell command and uses stdout as the model response. The included script `agent/local/ollama_provider.sh` integrates with Ollama.
- ManualProvider: writes `prompt.md` and waits for you to drop a diff at either `agent/artifacts/.../inbox.patch` or `agent/inbox/<cycle_basename>.patch`.

Environment hints for Ollama provider:
- `OLLAMA_MODEL` or `MODEL` to select a specific model
- `OLLAMA_HIDE_THINKING=1` to hide reasoning tokens (default)
- `OLLAMA_NUM_CTX` and `OLLAMA_KV_CACHE_TYPE` to tune context and cache

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
- Provider exec: `agent exec "<prompt>"`
- Models helper (Ollama): `agent models [--pull <model>]`

## Tips & Troubleshooting

- TUI missing? Install Textual: `pip install textual`
- Patch fails to apply? Set `patch.path_prefix` when your project is nested
- Missing tools? Install as needed:
  - `pipx install ruff bandit semgrep pip-audit`
  - `pipx install pytest coverage` (or use your environment)
- Using Ollama? Ensure a model is available: `ollama pull qwen2.5-coder:7b-instruct`

## Contributing

Contributions welcome! See `CONTRIBUTING.md` for guidelines. Please keep changes minimal, ensure analyzers/gates pass locally, and prioritize offline-first operation.

---

Built with care for offline workflows and transparent automation.
