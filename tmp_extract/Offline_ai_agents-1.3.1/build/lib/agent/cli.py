from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .providers import ProviderError, provider_from_config
from .providers.keys import KeyStore

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = REPO_ROOT / "agent"
CONFIG_PATH = AGENT_DIR / "config.json"
CONTROL_DIR = AGENT_DIR / "local" / "control"
STATE_DIR = AGENT_DIR / "state"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_control(name: str, content: str = "") -> None:
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    (CONTROL_DIR / f"{name}.cmd").write_text(content.strip(), encoding="utf-8")


def parse_duration(text: str) -> int:
    text = text.strip().lower()
    if text.endswith("h"):
        return int(float(text[:-1]) * 3600)
    if text.endswith("m"):
        return int(float(text[:-1]) * 60)
    if text.endswith("s"):
        return int(float(text[:-1]))
    return int(float(text))


def cmd_review(args: argparse.Namespace) -> int:
    scope = args.scope
    duration = parse_duration(args.duration) if args.duration else args.default_duration
    review_delay = parse_duration(args.post_review) if args.post_review else args.default_post_review
    payload = f"start scope={scope} dur={duration} review={review_delay}"
    write_control("session", payload)
    print(f"Scheduled session: {payload}")
    return 0


def cmd_commit(args: argparse.Namespace) -> int:
    if args.now:
        write_control("commit_now", "now")
        print("Commit scheduled immediately.")
    if args.on:
        write_control("auto_commit", "on")
        print("Auto-commit enabled.")
    if args.off:
        write_control("auto_commit", "off")
        print("Auto-commit disabled.")
    if args.cadence is not None:
        secs = parse_duration(args.cadence)
        write_control("cadence", str(secs))
        print(f"Commit cadence set to {secs}s")
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    cfg = load_config()
    try:
        provider = provider_from_config(cfg.get("provider", {}))
    except ProviderError as exc:
        print(f"provider error: {exc}")
        return 1

    if args.pull:
        if not shutil.which("ollama"):
            print("ollama CLI not found on PATH. Install from https://ollama.com/ first.")
            return 1
        print(f"Pulling Ollama model: {args.pull}")
        subprocess.run(["ollama", "pull", args.pull], check=False)

    if args.switch:
        cfg.setdefault("provider", {})["model"] = args.switch
        save_config(cfg)
        write_control("model", args.switch)
        print(f"Model switched to {args.switch}")
        return 0

    models = list(provider.list_models())
    if not models:
        print("No models available from current provider.")
        return 0
    for model in models:
        label = getattr(model, "name", str(model))
        print(label)
    return 0


def cmd_apikey(args: argparse.Namespace) -> int:
    store = KeyStore()
    name = args.name
    if args.action == "set":
        store.set(name, args.value)
        print(f"Stored API key for {name}")
    elif args.action == "get":
        value = store.get(name)
        if value:
            print(value)
        else:
            print(f"No key stored for {name}")
            return 1
    elif args.action == "clear":
        store.clear(name)
        print(f"Cleared API key for {name}")
    return 0


def cmd_exec(args: argparse.Namespace) -> int:
    cfg = load_config()
    try:
        provider = provider_from_config(cfg.get("provider", {}))
    except ProviderError as exc:
        print(f"provider error: {exc}")
        return 1
    qa_dir = AGENT_DIR / "local" / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    out = provider.generate_patch(args.prompt, str(qa_dir))
    output_path = qa_dir / "provider_output.txt"
    output_path.write_text(out or "", encoding="utf-8")
    print(output_path)
    return 0


def run_headless(args: argparse.Namespace) -> int:
    if args.max_cycles is not None:
        os.environ["AGENT_MAX_CYCLES"] = str(args.max_cycles)
    if args.cooldown_seconds is not None:
        os.environ["AGENT_COOLDOWN_SECONDS"] = str(args.cooldown_seconds)
    from . import run as agent_run

    agent_run.main()
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    commit_meta = read_json(STATE_DIR / "commit_scheduler.json")
    session_meta = read_json(STATE_DIR / "session.json")

    lines = ["Commit Scheduler"]
    if commit_meta:
        auto = "ON" if commit_meta.get("auto_commit", True) else "OFF"
        lines.append(f"  auto_commit : {auto}")
        cadence = commit_meta.get("cadence_seconds")
        if cadence is not None:
            lines.append(f"  cadence     : {int(cadence)}s")
        next_at = commit_meta.get("next_commit_at")
        if next_at:
            lines.append(f"  next_commit : {int(next_at)}")
    else:
        lines.append("  (no scheduler state yet)")

    lines.append("Session")
    if session_meta:
        lines.append(f"  status      : {session_meta.get('status', 'idle')}")
        scope = session_meta.get("active_scope")
        if scope:
            lines.append(f"  scope       : {scope}")
        review_eta = session_meta.get("review_eta")
        if review_eta:
            lines.append(f"  review_eta  : {int(review_eta)}")
    else:
        lines.append("  (session tracking disabled or not started)")

    print("\n".join(lines))
    return 0


def cmd_help(_: argparse.Namespace) -> int:
    cheat_sheet = """Agent CLI quick-start:\n\
  agent                       # launch Textual UI\n\
  agent --headless            # run loop in current shell\n\
  agent run --max-cycles=1    # single headless cycle\n\
  agent status                # show commit/session state\n\
  agent review <scope> --duration 30m\n\
  agent commit --now          # force commit if gate passes\n\
  agent models --pull llama3  # download Ollama model\n\
  agent apikey set openai sk-***\n\
  agent exec \"Investigate failing tests\"\n\
Tip: activate your virtualenv then export PATH=\"$PWD/scripts:$PATH\"."""
    print(cheat_sheet)
    return 0


def open_tui() -> int:
    try:
        from .view import launch_tui
    except RuntimeError as exc:
        print(f"TUI unavailable: {exc}")
        print("Use `agent --headless` for CLI mode or install Textual with `pip install textual`.\n"
              "Common commands:\n"
              "  agent run --max-cycles=1\n"
              "  agent review <scope> --duration 30m\n"
              "  agent commit --now\n")
        return 1

    return launch_tui()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent", description="Always-on offline-first coding agent")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--headless", action="store_true", help="Run headless loop")
    parser.add_argument("--cooldown-seconds", type=int, default=None)
    parser.add_argument("--max-cycles", type=int, default=None)

    subparsers = parser.add_subparsers(dest="cmd")

    helper = subparsers.add_parser("help", help="Print common CLI examples")
    helper.set_defaults(handler=cmd_help)

    review = subparsers.add_parser("review", help="Start a timeboxed review session")
    review.add_argument("scope", help="Scope path or topic")
    review.add_argument("--duration", help="Session duration (e.g. 45m)")
    review.add_argument("--post-review", help="Post-review delay (e.g. 120m)")
    review.add_argument("--default-duration", type=int, default=3600)
    review.add_argument("--default-post-review", type=int, default=3600)
    review.set_defaults(handler=cmd_review)

    commit = subparsers.add_parser("commit", help="Control commit scheduler")
    commit.add_argument("--now", action="store_true")
    commit.add_argument("--on", action="store_true")
    commit.add_argument("--off", action="store_true")
    commit.add_argument("--cadence", help="Set cadence (e.g. 1800s, 30m)")
    commit.set_defaults(handler=cmd_commit)

    models = subparsers.add_parser("models", help="List, pull, or switch models")
    models.add_argument("--pull", help="Download a model via ollama", default=None)
    models.add_argument("--switch", help="Set default model", default=None)
    models.set_defaults(handler=cmd_models)

    apikey = subparsers.add_parser("apikey", help="Manage hosted API keys")
    apikey.add_argument("action", choices=["set", "get", "clear"], help="Action to perform")
    apikey.add_argument("name", help="Key identifier (e.g. openai)")
    apikey.add_argument("value", nargs="?", default="", help="Secret value for set")
    apikey.set_defaults(handler=cmd_apikey)

    exec_cmd = subparsers.add_parser("exec", help="Send ad-hoc prompt to provider")
    exec_cmd.add_argument("prompt")
    exec_cmd.set_defaults(handler=cmd_exec)

    run_cmd = subparsers.add_parser("run", help="Run headless loop now")
    run_cmd.add_argument("--max-cycles", type=int, default=None)
    run_cmd.set_defaults(handler=run_headless)

    status_cmd = subparsers.add_parser("status", help="Show commit/session status")
    status_cmd.set_defaults(handler=cmd_status)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if hasattr(args, "handler"):
        return args.handler(args)

    if args.headless:
        return run_headless(args)
    return open_tui()


if __name__ == "__main__":
    raise SystemExit(main())
