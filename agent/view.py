def launch_tui() -> int:
    try:
        from .tui.app import launch_app
    except RuntimeError as exc:
        print(f"TUI unavailable: {exc}")
        return 1
    return launch_app()


if __name__ == "__main__":
    raise SystemExit(launch_tui())
