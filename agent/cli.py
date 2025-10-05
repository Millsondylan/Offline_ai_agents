import argparse
import os
import sys
from typing import List

from . import __version__


def _run_headless(args: argparse.Namespace) -> int:
    # Allow override cycles/cooldown via env for run.py
    if args.max_cycles is not None:
        os.environ["AGENT_MAX_CYCLES"] = str(args.max_cycles)
    if args.cooldown_seconds is not None:
        os.environ["AGENT_COOLDOWN_SECONDS"] = str(args.cooldown_seconds)
    from . import run as agent_run

    agent_run.main()
    return 0


def _open_tui(args: argparse.Namespace) -> int:
    try:
        from .view import launch_tui
    except Exception as e:
        print(f"TUI unavailable: {e}")
        return 1
    return launch_tui()


def _exec_prompt(args: argparse.Namespace) -> int:
    from .providers import ManualProvider, CommandProvider
    import json
    import time

    # Load config
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    cfg_path = os.path.join(repo_root, "agent", "config.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    provider_cfg = cfg.get("provider", {})
    if provider_cfg.get("type") == "command":
        p = CommandProvider(provider_cfg.get("command", {}).get("cmd", []), provider_cfg.get("command", {}).get("timeout_seconds", 600))
    else:
        p = ManualProvider()
    # Create QA artifacts
    ts = time.strftime("%Y%m%d-%H%M%S")
    qa_dir = os.path.join(repo_root, "agent", "local", "qa", ts)
    os.makedirs(qa_dir, exist_ok=True)
    prompt = args.prompt
    out = p.generate_patch(prompt, qa_dir)
    path = os.path.join(qa_dir, "provider_output.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out or "")
    print(path)
    return 0


def _models(args: argparse.Namespace) -> int:
    import shutil
    import subprocess
    if not shutil.which("ollama"):
        print("ollama not installed")
        return 1
    if args.pull:
        subprocess.run(["ollama", "pull", args.pull], check=False)
    proc = subprocess.run(["ollama", "list"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout.decode("utf-8", errors="replace"))
    return 0


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent", description="Always-on offline agent (TUI + headless)")
    p.add_argument("--version", action="store_true", help="Show version and exit")
    p.add_argument("--simple-cli", action="store_true", help="Force simple CLI mode")
    p.add_argument("--headless", action="store_true", help="Run without TUI (headless loop)")
    p.add_argument("--cooldown-seconds", type=int, default=None)
    p.add_argument("--max-cycles", type=int, default=None)

    sub = p.add_subparsers(dest="cmd")
    run_p = sub.add_parser("run", help="Run one or more cycles headless")
    run_p.add_argument("--enhance", action="store_true", help="Perform a full gated cycle")
    run_p.add_argument("--max-cycles", type=int, default=1)
    run_p.add_argument("--apply-patches", type=int, default=1)

    exec_p = sub.add_parser("exec", help="Run a non-interactive prompt against the provider")
    exec_p.add_argument("prompt", help="Prompt string")

    models_p = sub.add_parser("models", help="List or pull Ollama models")
    models_p.add_argument("--pull", help="Model to pull", default=None)

    return p


from typing import Optional


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = make_parser()
    args = p.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.cmd == "exec":
        return _exec_prompt(args)
    if args.cmd == "models":
        return _models(args)
    if args.cmd == "run":
        # Use headless runner; respect overrides
        if args.max_cycles is not None:
            os.environ["AGENT_MAX_CYCLES"] = str(args.max_cycles)
        if args.apply_patches is not None:
            # apply_patches is read from config; we rely on config, but hint via env is not currently supported
            pass
        return _run_headless(args)

    # Default: TUI unless --headless
    if args.headless:
        return _run_headless(args)
    return _open_tui(args)


if __name__ == "__main__":
    raise SystemExit(main())
