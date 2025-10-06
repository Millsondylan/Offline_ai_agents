"""Console entry point for the agent CLI control panel."""

from __future__ import annotations

from pathlib import Path

from agent_cli.app import main


def cli() -> None:
    main()


if __name__ == "__main__":
    cli()
