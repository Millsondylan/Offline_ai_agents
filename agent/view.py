def launch_tui() -> int:
    try:
        from .tui.simple_app import launch_simple_tui
    except RuntimeError as exc:
        print(f"TUI unavailable: {exc}")
        return 1
    return launch_simple_tui()


if __name__ == "__main__":
    raise SystemExit(launch_tui())
