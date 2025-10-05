def launch_tui() -> int:
    try:
        from .tui.app import AgentApp
    except Exception as e:
        print(f"TUI not available: {e}")
        return 1
    app = AgentApp()
    if hasattr(app, "run"):
        app.run()
    else:
        print("Textual not installed. Try: pip install textual")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(launch_tui())
