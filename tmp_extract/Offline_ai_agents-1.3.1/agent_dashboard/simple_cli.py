#!/usr/bin/env python3
"""Simple CLI interface for the agent when curses doesn't work."""

from agent_dashboard.core.real_agent_manager import RealAgentManager


class SimpleCLI:
    """Simple command-line interface for agent control."""

    def __init__(self):
        self.agent_manager = RealAgentManager()
        self.running = True

    def print_status(self):
        """Print current agent status."""
        state = self.agent_manager.get_state()
        print("\n--- Agent Status ---")
        print(f"Status: {state.status.value}")
        print(f"Model: {state.model}")
        print(f"Session: {state.session_id}")
        print(f"Cycle: {state.cycle}")
        print(f"Current Task: {state.current_task or 'None'}")
        print(f"Elapsed: {state.elapsed_seconds}s")
        print(f"Errors: {state.errors}, Warnings: {state.warnings}")

    def print_menu(self):
        """Print available commands."""
        print("\n--- Agent Dashboard (Simple CLI) ---")
        print("Commands:")
        print("  s/start  - Start agent")
        print("  p/pause  - Pause agent")
        print("  x/stop   - Stop agent")
        print("  t/task   - Add new task")
        print("  n/new    - Add new task (same as t)")
        print("  l/logs   - Show recent logs")
        print("  th/think - Show AI thinking/reasoning")
        print("  status   - Show agent status")
        print("  q/quit   - Exit dashboard")
        print("  h/help   - Show this menu")

    def show_logs(self):
        """Show recent log entries."""
        logs = self.agent_manager.get_logs()
        print("\n--- Recent Logs (last 10) ---")
        for log in logs[-10:]:
            timestamp = log.timestamp.strftime("%H:%M:%S")
            print(f"[{timestamp}] {log.level.name}: {log.message}")

    def show_thinking(self):
        """Show AI thinking/reasoning logs."""
        thoughts = self.agent_manager.get_thoughts()
        print("\n--- AI Thinking & Reasoning (last 20) ---")
        if not thoughts:
            print("No thinking logs available yet.")
            print("Start the agent with 's' to see AI reasoning.")
        else:
            for thought in thoughts[-20:]:
                timestamp = thought.timestamp.strftime("%H:%M:%S")
                cycle = f"C{thought.cycle}" if thought.cycle > 0 else "C?"
                print(f"[{timestamp}] {cycle}: {thought.content}")

    def add_task(self):
        """Add a new task with custom prompt."""
        print("\n=== Add New AI Task ===")
        print("Enter your task/prompt for the AI agent:")
        print("Examples:")
        print("  - Create a FastAPI endpoint for user authentication")
        print("  - Fix the bug in the payment processing module")
        print("  - Add unit tests for the user service")
        print("  - Implement a simple calculator with GUI")
        print("")
        description = input("Task/Prompt> ").strip()
        if description:
            task = self.agent_manager.add_task(description)
            print(f"✓ Added task #{task.id}: {task.description[:60]}...")
            print("✓ The agent will work on this when started with 's'")
        else:
            print("Task description cannot be empty.")

    def run(self):
        """Run the simple CLI interface."""
        print("=== Agent Dashboard (Simple CLI Mode) ===")
        print("Curses interface not available, using simple text interface.")

        self.print_status()
        self.print_menu()

        while self.running:
            try:
                command = input("\nCommand> ").strip().lower()

                if command in ['q', 'quit', 'exit']:
                    self.running = False
                    print("Exiting dashboard...")

                elif command in ['s', 'start']:
                    self.agent_manager.start()
                    print("✓ Agent started")

                elif command in ['p', 'pause']:
                    self.agent_manager.pause()
                    print("✓ Agent pause requested")

                elif command in ['x', 'stop']:
                    self.agent_manager.stop()
                    print("✓ Agent stop requested")

                elif command in ['t', 'task']:
                    self.add_task()

                elif command in ['n', 'new']:
                    self.add_task()

                elif command in ['l', 'logs']:
                    self.show_logs()

                elif command in ['th', 'think', 'thinking']:
                    self.show_thinking()

                elif command == 'status':
                    self.print_status()

                elif command in ['h', 'help']:
                    self.print_menu()

                elif command == '':
                    # Empty command, just refresh status
                    self.print_status()

                else:
                    print(f"Unknown command: {command}")
                    print("Type 'h' for help or 'q' to quit")

            except KeyboardInterrupt:
                print("\nCtrl+C pressed. Type 'q' to quit.")
            except EOFError:
                print("\nEOF detected. Exiting...")
                self.running = False

def main():
    """Entry point for simple CLI."""
    cli = SimpleCLI()
    cli.run()

if __name__ == "__main__":
    main()
