#!/usr/bin/env python3
"""Enhanced interactive CLI interface with better UX when curses fails."""

import time
import threading
import os
import sys
from datetime import datetime
from agent_dashboard.core.real_agent_manager import RealAgentManager
from agent_dashboard.core.models import AgentStatus

class EnhancedCLI:
    """Enhanced command-line interface with better interactivity."""

    def __init__(self):
        self.agent_manager = RealAgentManager()
        self.running = True
        self.auto_refresh = False
        self.last_cycle = 0

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Print a nice header."""
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 25 + "🤖 AI AGENT DASHBOARD" + " " * 31 + "║")
        print("╚" + "═" * 78 + "╝")
        print()

    def print_status_box(self):
        """Print current agent status in a nice box."""
        state = self.agent_manager.get_state()

        print("┌─ Agent Status " + "─" * 62 + "┐")
        print(f"│ Status: {self._colorize_status(state.status.value):<20} Model: {state.model:<35} │")
        print(f"│ Session: {state.session_id:<18} Cycle: {state.cycle:<35} │")
        print(f"│ Current Task: {(state.current_task or 'None'):<56} │")
        print(f"│ Elapsed: {state.elapsed_seconds}s{'':<10} Errors: {state.errors}, Warnings: {state.warnings:<25} │")
        print("└" + "─" * 76 + "┘")
        print()

    def _colorize_status(self, status):
        """Add color to status based on type."""
        colors = {
            'RUNNING': '\033[92m' + status + '\033[0m',  # Green
            'IDLE': '\033[94m' + status + '\033[0m',      # Blue
            'PAUSED': '\033[93m' + status + '\033[0m',    # Yellow
            'ERROR': '\033[91m' + status + '\033[0m',     # Red
        }
        return colors.get(status, status)

    def print_menu_grid(self):
        """Print menu options in a nice grid layout."""
        print("┌─ Available Commands " + "─" * 55 + "┐")
        print("│                                                                          │")
        print("│  🚀 [s] Start Agent     ⏸  [p] Pause Agent     🛑 [x] Stop Agent       │")
        print("│  📝 [t] Add Task        🧠 [th] AI Thinking    📊 [logs] View Logs     │")
        print("│  📈 [status] Refresh    🔄 [auto] Auto-refresh ❓ [h] Help             │")
        print("│  🎯 [watch] Live View   📋 [tasks] Task List   🚪 [q] Quit             │")
        print("│                                                                          │")
        print("└" + "─" * 74 + "┘")
        print()

    def show_live_thinking(self):
        """Show real-time AI thinking with live updates."""
        print("🧠 === AI THINKING & REASONING (Live View) ===")
        print("Press Ctrl+C to return to menu...\n")

        try:
            last_count = 0
            while True:
                thoughts = self.agent_manager.get_thoughts()
                if len(thoughts) > last_count:
                    # Show new thoughts
                    for thought in thoughts[last_count:]:
                        timestamp = thought.timestamp.strftime("%H:%M:%S")
                        cycle = f"C{thought.cycle}" if thought.cycle > 0 else "C?"
                        content = thought.content[:100] + "..." if len(thought.content) > 100 else thought.content
                        print(f"🔥 [{timestamp}] {cycle}: {content}")
                    last_count = len(thoughts)

                # Show agent status indicator
                state = self.agent_manager.get_state()
                if state.status == AgentStatus.RUNNING:
                    print("⚡ Agent is actively thinking...", end='\r')
                else:
                    print(" " * 30, end='\r')

                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\nReturning to main menu...")
            time.sleep(1)

    def show_task_manager(self):
        """Interactive task management."""
        while True:
            print("\n📋 === TASK MANAGER ===")
            print("1. Add new task")
            print("2. View pending tasks")
            print("3. Clear completed tasks")
            print("4. Return to main menu")

            choice = input("\nSelect option (1-4): ").strip()

            if choice == '1':
                self.add_task_interactive()
            elif choice == '2':
                self.show_task_list()
            elif choice == '3':
                print("✓ Task cleanup functionality coming soon...")
            elif choice == '4':
                break
            else:
                print("❌ Invalid option. Please choose 1-4.")

    def add_task_interactive(self):
        """Interactive task creation with examples."""
        print("\n🎯 === ADD NEW AI TASK ===")
        print("\n💡 Example tasks:")
        print("  • Create a REST API for user management")
        print("  • Fix the authentication bug in login.py")
        print("  • Add comprehensive tests for the payment module")
        print("  • Implement a responsive dashboard with charts")
        print("  • Optimize database queries for better performance")
        print("  • Add error handling and logging to the service")
        print()

        description = input("📝 Enter your task/prompt: ").strip()
        if description:
            task = self.agent_manager.add_task(description)
            print(f"\n✅ Task #{task.id} added successfully!")
            print(f"📋 Description: {task.description}")
            print("🚀 Start the agent with 's' to begin work on this task.")
        else:
            print("❌ Task description cannot be empty.")

        input("\nPress Enter to continue...")

    def show_task_list(self):
        """Show list of tasks."""
        print("\n📋 Current Tasks:")
        print("-" * 50)
        print("📌 Task list functionality coming soon...")
        input("\nPress Enter to continue...")

    def auto_refresh_mode(self):
        """Enable auto-refresh mode with live updates."""
        print("🔄 Auto-refresh mode enabled! Press Ctrl+C to stop...\n")

        try:
            while True:
                self.clear_screen()
                self.print_header()
                self.print_status_box()

                # Show recent activity
                thoughts = self.agent_manager.get_thoughts()
                if thoughts:
                    print("🔥 Recent AI Activity:")
                    for thought in thoughts[-3:]:
                        timestamp = thought.timestamp.strftime("%H:%M:%S")
                        cycle = f"C{thought.cycle}"
                        content = thought.content[:60] + "..." if len(thought.content) > 60 else thought.content
                        print(f"   [{timestamp}] {cycle}: {content}")
                    print()

                print("🔄 Auto-refreshing every 2 seconds... (Ctrl+C to stop)")
                time.sleep(2)

        except KeyboardInterrupt:
            print("\n\n✓ Auto-refresh stopped.")
            time.sleep(1)

    def run(self):
        """Run the enhanced CLI interface."""
        self.clear_screen()
        self.print_header()

        print("🎉 Welcome to the Enhanced Agent Dashboard!")
        print("💡 The curses TUI isn't available, but this interface provides full functionality!")
        print()

        while self.running:
            self.print_status_box()
            self.print_menu_grid()

            try:
                command = input("🎮 Command> ").strip().lower()

                if command in ['q', 'quit', 'exit']:
                    self.running = False
                    print("👋 Goodbye! Agent dashboard shutting down...")

                elif command in ['s', 'start']:
                    self.agent_manager.start()
                    print("🚀 Agent started! Use 'watch' for live updates.")

                elif command in ['p', 'pause']:
                    self.agent_manager.pause()
                    print("⏸  Agent pause requested.")

                elif command in ['x', 'stop']:
                    self.agent_manager.stop()
                    print("🛑 Agent stop requested.")

                elif command in ['t', 'task', 'tasks']:
                    self.show_task_manager()

                elif command in ['th', 'think', 'thinking']:
                    thoughts = self.agent_manager.get_thoughts()
                    if thoughts:
                        print("\n🧠 Recent AI Thinking:")
                        for thought in thoughts[-10:]:
                            timestamp = thought.timestamp.strftime("%H:%M:%S")
                            cycle = f"C{thought.cycle}"
                            print(f"   [{timestamp}] {cycle}: {thought.content}")
                    else:
                        print("🤔 No AI thinking logs yet. Start the agent to see reasoning!")

                elif command in ['logs', 'log']:
                    logs = self.agent_manager.get_logs()
                    print("\n📊 Recent Logs:")
                    for log in logs[-10:]:
                        timestamp = log.timestamp.strftime("%H:%M:%S")
                        print(f"   [{timestamp}] {log.level.name}: {log.message}")

                elif command == 'status':
                    print("🔄 Status refreshed!")

                elif command in ['auto', 'autorefresh']:
                    self.auto_refresh_mode()

                elif command in ['watch', 'live']:
                    self.show_live_thinking()

                elif command in ['h', 'help']:
                    print("📖 Help: Use the commands shown in the menu above!")

                elif command == '':
                    # Empty command, just refresh
                    self.clear_screen()
                    self.print_header()

                else:
                    print(f"❌ Unknown command: '{command}'. Type 'h' for help.")

            except KeyboardInterrupt:
                print("\n\n👋 Ctrl+C detected. Type 'q' to quit gracefully.")
            except EOFError:
                print("\n\n👋 EOF detected. Exiting...")
                break

        print("✨ Dashboard session ended.")