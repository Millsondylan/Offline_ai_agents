#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")"/.. && pwd)
LOG_DIR="$ROOT_DIR/run_logs"
mkdir -p "$LOG_DIR"

echo "starting forever loop"
while true; do
  "$ROOT_DIR/scripts/agent" --headless --cooldown-seconds=0 >>"$LOG_DIR/agent.forever.out.log" 2>>"$LOG_DIR/agent.forever.err.log" || true
  sleep 2
done

