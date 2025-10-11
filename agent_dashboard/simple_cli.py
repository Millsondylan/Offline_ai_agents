#!/usr/bin/env python3
"""Rich text fallback for the agent dashboard when curses is unavailable."""

from __future__ import annotations

import json
import os
from textwrap import shorten

from agent_dashboard.core.real_agent_manager import RealAgentManager
from agent_dashboard.core.models import AgentStatus, TaskStatus
from agent_dashboard.core.model_downloader import ModelDownloader


class SimpleCLI:
    """Interactive plain-text dashboard that mirrors the main menu layout."""

    MENU_CONFIG = [
        ("T", "Task Manager", "tasks"),
        ("S", "Start/Pause", "start_pause"),
        ("X", "Stop Agent", "stop"),
        ("A", "AI Thinking", "thinking"),
        ("L", "Logs", "logs"),
        ("C", "Code Viewer", "code"),
        ("M", "Model Config", "model"),
        ("K", "Configure API Keys", "api_keys"),
        ("V", "Verification", "verification"),
        ("H", "Help", "help"),
        ("CTRL+Q", "Exit", "exit"),
    ]

    DASHBOARD_WIDTH = 96

    def __init__(self) -> None:
        self.agent_manager = RealAgentManager()
        self.running = True
        self.selected_index = 0

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def render_dashboard(self) -> None:
        """Render a textual representation of the dashboard layout."""
        width = self.DASHBOARD_WIDTH
        state = self.agent_manager.get_state()

        print("\n" + "=" * width)
        header_1 = (
            f" Model: {state.model}   Session: {state.session_id}   "
            f"Cycle: #{state.cycle} ({state.status.value})   Elapsed: {state.elapsed_seconds}s"
        )
        header_2 = (
            f" Status: {state.status.value}   Mode: {state.mode.value}   "
            f"Progress: {state.progress_percent}%   "
            f"Tasks: {len(self.agent_manager.tasks)}   Errors: {state.errors}"
        )
        print(header_1[:width])
        print(header_2[:width])
        print("-" * width)

        # Menu block
        print("** Main Menu **")
        for idx, (shortcut, title, _) in enumerate(self.MENU_CONFIG, start=1):
            pointer = "➤" if (idx - 1) == self.selected_index else " "
            shortcut_label = f"[{shortcut}]".ljust(10)
            print(f" {pointer} {idx}. {title.ljust(18)} {shortcut_label}")

        print("-" * width)

        # Active panel content
        panel_title = self.MENU_CONFIG[self.selected_index][1]
        print(f"** Active Panel: {panel_title} **")
        for line in self._panel_content(self.MENU_CONFIG[self.selected_index][2], width):
            print(f"  {line[:width-2]}")

        print("-" * width)

        # Sidebar-style summary
        sidebar_lines = self._sidebar_summary(state)
        print("** Status Summary **")
        for line in sidebar_lines:
            print(f"  {line[:width-2]}")

        print("-" * width)
        print(
            "Hint: use 'up'/'down' or number keys to move, 'enter' to activate. "
            "Classic commands (s/p/x/t/l/th/k) still work."
        )
        print("=" * width)

    def _sidebar_summary(self, state) -> list[str]:
        """Compose sidebar text showing quick metrics."""
        lines = [
            f"Lifecycle: {state.status.value}",
            f"Model: {state.model}",
            f"Active Task: {state.current_task or 'None'}",
            f"Elapsed: {state.elapsed_seconds}s",
            f"Warnings: {state.warnings}",
        ]
        if state.verification_checks:
            passed = sum(1 for chk in state.verification_checks if chk.get("status") == "passed")
            total = len(state.verification_checks)
            lines.append(f"Verification: {passed}/{total} passed")
        return lines

    def _panel_content(self, panel_key: str, width: int) -> list[str]:
        """Return content lines for the currently selected panel."""
        if panel_key == "tasks":
            return self._panel_tasks(width)
        if panel_key == "start_pause":
            return self._panel_start_pause()
        if panel_key == "stop":
            return ["Stop the agent immediately.", "Shortcut: X or command 'x'."]
        if panel_key == "thinking":
            return self._panel_thinking(width)
        if panel_key == "logs":
            return self._panel_logs(width)
        if panel_key == "code":
            return self._panel_code(width)
        if panel_key == "model":
            return self._panel_model(width)
        if panel_key == "verification":
            return self._panel_verification(width)
        if panel_key == "help":
            return self._panel_help()
        if panel_key == "exit":
            return ["Exit dashboard and return to shell.", "Shortcut: CTRL+Q or command 'q'."]
        return ["Panel not implemented."]

    def _panel_tasks(self, width: int) -> list[str]:
        tasks = self.agent_manager.tasks
        if not tasks:
            return ["No tasks yet. Press 't' to add a new task."]

        lines = []
        active_id = self.agent_manager.active_task_id
        for task in tasks[:8]:
            marker = "★" if task.id == active_id else " "
            status = task.status.value if isinstance(task.status, TaskStatus) else str(task.status)
            desc = shorten(task.description, width=width - 20, placeholder="…")
            created = task.created_at.strftime("%Y-%m-%d %H:%M")
            lines.append(f"{marker} #{task.id:03d} {status:<11} {desc} ({created})")
        if len(tasks) > 8:
            lines.append(f"... and {len(tasks) - 8} more tasks.")
        return lines

    def _panel_start_pause(self) -> list[str]:
        state = self.agent_manager.get_state()
        if state.status == AgentStatus.RUNNING:
            return [
                "Agent is running continuous cycles.",
                "Type 'p' to request a pause (logs a warning).",
                "Type 'x' to stop or 'th' to inspect reasoning.",
            ]
        return [
            f"Agent status: {state.status.value}",
            "Type 's' to start autonomous cycles.",
            "Provide tasks first using 't'.",
        ]

    def _panel_thinking(self, width: int) -> list[str]:
        thoughts = list(self.agent_manager.get_thoughts())[-6:]
        if not thoughts:
            return ["No thinking logs yet. Start the agent to see reasoning output."]
        lines = []
        for thought in thoughts:
            timestamp = thought.timestamp.strftime("%H:%M:%S")
            cycle = f"C{thought.cycle:03d}"
            content = shorten(thought.content, width=width - 20, placeholder="…")
            lines.append(f"{timestamp} | {cycle} | {content}")
        return lines

    def _panel_logs(self, width: int) -> list[str]:
        logs = list(self.agent_manager.get_logs())[-6:]
        if not logs:
            return ["No logs recorded yet."]
        lines = []
        for log in logs:
            timestamp = log.timestamp.strftime("%H:%M:%S")
            message = shorten(log.message, width=width - 18, placeholder="…")
            lines.append(f"{timestamp} [{log.level.name}] {message}")
        return lines

    def _panel_code(self, width: int) -> list[str]:
        repo = self.agent_manager.repo_root
        artifacts = repo / "agent" / "artifacts"
        cycle_dirs = []
        if artifacts.exists():
            cycle_dirs = sorted(
                [d for d in artifacts.iterdir() if d.is_dir()],
                key=lambda d: d.name,
                reverse=True,
            )[:3]

        lines = ["Review recent diffs and findings:"]
        if not cycle_dirs:
            lines.append("No artifacts found yet. Run the agent to generate diffs.")
            return lines

        for cycle in cycle_dirs:
            diff_files = list(cycle.glob("*.patch")) + list(cycle.glob("*.diff"))
            if diff_files:
                lines.append(f"{cycle.name}: {diff_files[0].name}")
            else:
                lines.append(f"{cycle.name}: No diff artifacts.")
        lines.append("Open these files manually or inspect via git diff.")
        return lines

    def _panel_model(self, width: int) -> list[str]:
        config_path = self.agent_manager.repo_root / "agent" / "config.json"
        if not config_path.exists():
            return ["No agent/config.json found. Configure models via CLI."]
        try:
            data = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            return ["Failed to parse agent/config.json (invalid JSON)."]

        lines = []
        provider = data.get("provider", {})
        if isinstance(provider, dict):
            lines.append(f"Provider: {provider.get('type', 'unknown')}")
            lines.append(f"Model: {provider.get('model', 'unspecified')}")
        models = data.get("available_models") or data.get("models")
        if isinstance(models, list):
            preview = ", ".join(models[:4])
            if len(models) > 4:
                preview += f", +{len(models) - 4} more"
            lines.append(f"Available: {preview}")
        params = data.get("parameters", {})
        if isinstance(params, dict):
            for key in ("temperature", "max_tokens", "top_p"):
                if key in params:
                    lines.append(f"{key.replace('_', ' ').title()}: {params[key]}")
        lines.append("")
        lines.append("API Connectivity:")
        for entry in ModelDownloader.API_PROVIDERS:
            env_var, value, source = ModelDownloader._resolve_api_key(entry)
            if value:
                status = "env" if source == "env" else "stored"
                label = entry.get("label", entry["type"].title())
                descriptor = env_var if status == "env" else "vault"
                lines.append(f"  {label}: configured via {descriptor}")
            else:
                lines.append(f"  {entry.get('label', entry['type'].title())}: missing key")
        return lines or ["Config file parsed but no recognized fields."]

    def _panel_verification(self, width: int) -> list[str]:
        state = self.agent_manager.get_state()
        checks = state.verification_checks
        if not checks:
            return ["No verification results recorded yet."]
        lines = []
        for check in checks[:6]:
            name = shorten(check.get("name", "check"), width=width - 20, placeholder="…")
            status = check.get("status", "unknown")
            duration = check.get("duration", check.get("duration_ms"))
            duration_txt = f"{duration}ms" if duration is not None else ""
            lines.append(f"{status.upper():<7} {name} {duration_txt}")
        if len(checks) > 6:
            lines.append(f"... and {len(checks) - 6} more checks.")
        return lines

    def _panel_help(self) -> list[str]:
        return [
            "Use the number keys or 'up'/'down' then 'enter' to open a panel.",
            "Command shortcuts:",
            "  s/start  - Start agent",
            "  p/pause  - Pause (logs warning)",
            "  x/stop   - Stop agent",
            "  t/new    - Add task",
            "  l/logs   - Detailed logs view",
            "  th       - Detailed thinking view",
            "  k/keys   - Configure API keys",
            "  q/quit   - Exit dashboard",
        ]

    # ------------------------------------------------------------------
    # Detailed views triggered from menu selection
    # ------------------------------------------------------------------
    def show_logs(self, limit: int = 10) -> None:
        """Show expanded log entries."""
        logs = list(self.agent_manager.get_logs())[-limit:]
        print(f"\n--- Recent Logs (last {limit}) ---")
        if not logs:
            print("No logs recorded yet.")
            return
        for log in logs:
            timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {log.level.name}: {log.message}")

    def show_thinking(self, limit: int = 20) -> None:
        """Show extended AI thinking list."""
        thoughts = list(self.agent_manager.get_thoughts())[-limit:]
        print(f"\n--- AI Thinking & Reasoning (last {limit}) ---")
        if not thoughts:
            print("No thinking logs available yet. Start the agent with 's'.")
            return
        for thought in thoughts:
            timestamp = thought.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            cycle = f"C{thought.cycle}" if thought.cycle else "C?"
            print(f"[{timestamp}] {cycle}: {thought.content}")

    def show_tasks(self) -> None:
        """Show full task list."""
        tasks = self.agent_manager.tasks
        print("\n--- Task Manager ---")
        if not tasks:
            print("No tasks yet. Add one with 't'.")
            return
        active_id = self.agent_manager.active_task_id
        for task in tasks:
            marker = "[ACTIVE]" if task.id == active_id else "         "
            created = task.created_at.strftime("%Y-%m-%d %H:%M")
            status = task.status.value if isinstance(task.status, TaskStatus) else str(task.status)
            print(f"#{task.id:03d} {marker} {status:<12} {task.description} ({created})")

    # ------------------------------------------------------------------
    # Menu navigation helpers
    # ------------------------------------------------------------------
    def move_selection(self, delta: int) -> None:
        self.selected_index = (self.selected_index + delta) % len(self.MENU_CONFIG)

    def set_selection(self, index: int) -> None:
        if 0 <= index < len(self.MENU_CONFIG):
            self.selected_index = index

    def activate_selection(self) -> None:
        panel_key = self.MENU_CONFIG[self.selected_index][2]
        if panel_key == "tasks":
            self.show_tasks()
        elif panel_key == "start_pause":
            self._toggle_start_pause()
        elif panel_key == "stop":
            self.agent_manager.stop()
            print("✓ Agent stop requested")
        elif panel_key == "thinking":
            self.show_thinking()
        elif panel_key == "logs":
            self.show_logs()
        elif panel_key == "api_keys":
            self.configure_api_keys()
        elif panel_key == "verification":
            self.agent_manager.run_verification()
            print("Verification run queued (awaiting agent cycles)")
        elif panel_key == "help":
            for line in self._panel_help():
                print(line)
        elif panel_key == "exit":
            self.running = False
            print("Exiting dashboard...")

    def _toggle_start_pause(self) -> None:
        state = self.agent_manager.get_state()
        if state.status == AgentStatus.RUNNING:
            self.agent_manager.pause()
            print("Pause requested (autonomous agent keeps running but logs the request).")
        else:
            self.agent_manager.start()
            print("✓ Agent started")

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------
    def configure_api_keys(self) -> None:
        """Prompt the user to enter or update API keys."""
        entries = ModelDownloader.API_PROVIDERS
        print("\n=== Configure API Keys ===")
        print("Choose a provider to add/update credentials:")

        for idx, entry in enumerate(entries, start=1):
            env_var, value, source = ModelDownloader._resolve_api_key(entry)
            stored = ModelDownloader.get_stored_api_key(entry["type"])
            if value:
                if source == "env":
                    status = f"using {env_var}"
                else:
                    status = "stored securely"
            elif stored:
                status = "stored (inactive)"
            else:
                status = "not set"
            print(f"  {idx}. {entry['label']} [{status}]")

        choice = input("Select provider number (blank to cancel): ").strip()
        if not choice:
            print("No changes made.")
            return

        if not choice.isdigit() or not (1 <= int(choice) <= len(entries)):
            print("Invalid selection.")
            return

        provider_entry = entries[int(choice) - 1]
        key_prompt = f"Enter {provider_entry['label']} API key (blank to cancel): "
        api_key = input(key_prompt).strip()
        if not api_key:
            print("No key provided. Keeping existing configuration.")
            return

        ModelDownloader.store_api_key(provider_entry["type"], api_key)
        primary_env = provider_entry["env"][0]
        os.environ[primary_env] = api_key

        info = ModelDownloader._configure_api_provider(provider_entry["type"], provider_entry["model"], "stored")
        self.agent_manager.provider_info = info
        self.agent_manager.state.model = f"{info.provider_type}:{info.model}"
        print(f"✓ Stored API key for {provider_entry['label']}.")

    def add_task(self) -> None:
        """Prompt user to create a new task."""
    def add_task(self) -> None:
        """Prompt user to create a new task."""
        print("\n=== Add New AI Task ===")
        print("Enter the work item or prompt the agent should execute.")
        print("Example: Implement authentication API, Fix failing tests, etc.")
        description = input("Task/Prompt> ").strip()
        if description:
            task = self.agent_manager.add_task(description)
            print(f"✓ Added task #{task.id}: {description}")
        else:
            print("Task description cannot be empty.")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Run the simple CLI interface."""
        print("=== Agent Dashboard (Simple CLI Mode) ===")
        print("Curses interface failed; using rich text fallback.\n")
        self.render_dashboard()

        while self.running:
            try:
                command = input("\nCommand> ").strip().lower()

                if command in {"q", "quit", "exit", "ctrl+q"}:
                    self.running = False
                    print("Exiting dashboard...")
                    break

                if command in {"up", "k"}:
                    self.move_selection(-1)
                    self.render_dashboard()
                    continue

                if command in {"down", "j"}:
                    self.move_selection(1)
                    self.render_dashboard()
                    continue

                if command in {"enter", "open", "view"}:
                    self.activate_selection()
                    if self.running:
                        self.render_dashboard()
                    continue

                if command.isdigit():
                    self.set_selection(int(command) - 1)
                    self.render_dashboard()
                    continue

                if command in {"s", "start"}:
                    self.agent_manager.start()
                    print("✓ Agent started")
                    self.render_dashboard()
                    continue

                if command in {"p", "pause"}:
                    self.agent_manager.pause()
                    print("Pause requested (agent keeps running).")
                    self.render_dashboard()
                    continue

                if command in {"x", "stop"}:
                    self.agent_manager.stop()
                    print("✓ Agent stop requested")
                    self.render_dashboard()
                    continue

                if command in {"t", "task", "n", "new"}:
                    self.add_task()
                    self.render_dashboard()
                    continue

                if command in {"k", "keys"}:
                    self.configure_api_keys()
                    self.render_dashboard()
                    continue

                if command in {"l", "logs"}:
                    self.show_logs()
                    self.render_dashboard()
                    continue

                if command in {"th", "think", "thinking"}:
                    self.show_thinking()
                    self.render_dashboard()
                    continue

                if command == "status":
                    self.render_dashboard()
                    continue

                if command in {"h", "help"}:
                    for line in self._panel_help():
                        print(line)
                    self.render_dashboard()
                    continue

                if command == "":
                    self.render_dashboard()
                    continue

                print(f"Unknown command: {command}")
                print("Type 'h' for help or use the menu navigation keys.")

            except KeyboardInterrupt:
                print("\nCtrl+C pressed. Type 'q' to quit.")
            except EOFError:
                print("\nEOF detected. Exiting...")
                self.running = False


def main() -> None:
    """Entry point for simple CLI."""
    SimpleCLI().run()


if __name__ == "__main__":
    main()
