from __future__ import annotations

from .app import AgentTUI


def main() -> int:
    app = AgentTUI()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
