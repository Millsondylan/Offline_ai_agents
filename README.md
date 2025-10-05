Agent: Always-On, Offline-First (TUI + Headless)

- Launch TUI:
  - export PATH="$PWD/scripts:$PATH"; agent
- Headless run (one cycle):
  - scripts/agent run --max-cycles=1
- Start background loop:
  - scripts/agent-start
- Stop background loop:
  - scripts/agent-stop

Artifacts are written under `agent/artifacts/cycle_<N>_<timestamp>` and include `prompt.md`, provider output, proposed/applied patches, gate reports, and git plumbing metadata.

