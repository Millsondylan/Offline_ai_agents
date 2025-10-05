#!/usr/bin/env bash
set -euo pipefail

# Read full prompt from stdin
PROMPT=$(cat)

ensure_ollama() {
  if ! ollama list >/dev/null 2>&1; then
    nohup ollama serve >/dev/null 2>&1 &
    # Wait for ollama to be responsive
    for i in {1..60}; do
      if ollama list >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
  fi
}

pick_model() {
  local preferred=(
    "qwen2.5-coder:7b-instruct"
    "deepseek-coder:6.7b-instruct"
    "deepseek-coder:6.7b"
    "qwen2.5:3b-instruct"
  )
  local available
  available=$(ollama list 2>/dev/null | awk 'NR>1{print $1}') || available=""
  for m in "${preferred[@]}"; do
    if echo "$available" | grep -qx "$m"; then
      echo "$m"
      return 0
    fi
  done
  # Fallback to first available
  if [ -n "$available" ]; then
    echo "$available" | head -n1
    return 0
  fi
  return 1
}

ensure_ollama

# Allow override via env var OLLAMA_MODEL or MODEL
if [ -n "${OLLAMA_MODEL:-}" ]; then
  OVERRIDE_MODEL="$OLLAMA_MODEL"
elif [ -n "${MODEL:-}" ]; then
  OVERRIDE_MODEL="$MODEL"
else
  OVERRIDE_MODEL=""
fi

if [ -n "$OVERRIDE_MODEL" ]; then
  # Validate availability
  available=$(ollama list 2>/dev/null | awk 'NR>1{print $1}') || available=""
  if echo "$available" | grep -qx "$OVERRIDE_MODEL"; then
    MODEL="$OVERRIDE_MODEL"
  else
    echo "Requested model '$OVERRIDE_MODEL' not available; falling back" 1>&2
    MODEL=""
  fi
fi

if [ -z "${MODEL:-}" ]; then
  MODEL=$(pick_model)
fi

if [ -z "${MODEL:-}" ]; then
  echo "No Ollama models available" 1>&2
  exit 1
fi

# Run model non-interactively; allow toggling thinking output
FLAGS=("--nowordwrap")
if [ "${OLLAMA_HIDE_THINKING:-1}" = "1" ]; then
  FLAGS+=("--hidethinking")
fi
OLLAMA_NUM_CTX=${OLLAMA_NUM_CTX:-8192} \
OLLAMA_KV_CACHE_TYPE=${OLLAMA_KV_CACHE_TYPE:-cpu} \
ollama run "$MODEL" "${FLAGS[@]}" "$PROMPT"
