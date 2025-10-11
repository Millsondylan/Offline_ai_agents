def launch_tui() -> int:
    try:
        from .tui.app import launch_app
    except ImportError as exc:
        print(f"TUI unavailable: {exc}")
        print("Install required dependencies: pip install textual")
        return 1
    except Exception as exc:
        print(f"TUI error: {exc}")
        return 1
    return launch_app()


if __name__ == "__main__":
    raise SystemExit(launch_tui())
