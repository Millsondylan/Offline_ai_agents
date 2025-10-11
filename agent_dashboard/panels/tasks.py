"""Task manager panel."""

import curses
from agent_dashboard.panels.base import BasePanel


class TaskPanel(BasePanel):
    """Task management panel."""

    def __init__(self, agent_manager, theme_manager):
        super().__init__("Task Manager", agent_manager, theme_manager)
        self.selected_index = 0

    def render(self, win, start_y: int, start_x: int, height: int, width: int):
        """Render task list."""
        tasks = self.agent_manager.tasks

        y = start_y + 1
        x = start_x + 2

        # Instructions
        self.safe_addstr(win, y, x, "Task Manager - AI Prompts for Autonomous Execution",
                       self.theme_manager.get('highlight'))
        y += 1
        self.safe_addstr(win, y, x, "Commands: N=New Task, D=Delete, A=Activate, ↑↓=Navigate",
                       self.theme_manager.get('info'))
        y += 2

        if not tasks:
            self.safe_addstr(win, y, x, "No tasks yet. Press N to add your first AI prompt.",
                           self.theme_manager.get('warning'))
            return

        # Header
        self.safe_addstr(win, y, x, "ID  Status        Description",
                        self.theme_manager.get('highlight'))
        y += 1
        self.safe_addstr(win, y, x, "──  ────────────  ─────────────────────────")
        y += 1

        # Task list
        for i, task in enumerate(tasks):
            if i < self.scroll_offset:
                continue
            if y >= start_y + height - 2:
                break

            prefix = "→ " if i == self.selected_index else "  "
            status_icon = {
                "Pending": "○",
                "In Progress": "◐",
                "Completed": "●",
                "Failed": "✗",
            }.get(task.status.value, "?")

            text = f"{prefix}{task.id:2} {status_icon} {task.status.value:12} {task.description[:30]}"

            attr = self.theme_manager.get('selected') if i == self.selected_index else curses.A_NORMAL
            self.safe_addstr(win, y, x, text, attr)
            y += 1

    def handle_key(self, key: int) -> bool:
        """Handle task panel keys."""
        tasks = self.agent_manager.tasks

        if key == curses.KEY_UP and self.selected_index > 0:
            self.selected_index -= 1
            if self.selected_index < self.scroll_offset:
                self.scroll_offset -= 1
            return True

        elif key == curses.KEY_DOWN and self.selected_index < len(tasks) - 1:
            self.selected_index += 1
            return True

        elif key in (ord('n'), ord('N')):
            # Create new task with user input
            return self.create_new_task()

        elif key in (ord('d'), ord('D')) and tasks:
            # Delete selected task
            if 0 <= self.selected_index < len(tasks):
                task = tasks[self.selected_index]
                self.agent_manager.delete_task(task.id)
                if self.selected_index >= len(self.agent_manager.tasks):
                    self.selected_index = max(0, len(self.agent_manager.tasks) - 1)
            return True

        elif key in (ord('a'), ord('A')) and tasks:
            # Activate selected task
            if 0 <= self.selected_index < len(tasks):
                task = tasks[self.selected_index]
                self.agent_manager.set_active_task(task.id)
            return True

        return False

    def create_new_task(self):
        """Create a new task with user input."""
        win = getattr(self, "stdscr", None)

        def _fallback_input() -> bool:
            try:
                description = input("Task description: ").strip()
            except EOFError:
                return False
            if not description:
                return False
            self.agent_manager.add_task(description)
            self.selected_index = len(self.agent_manager.tasks) - 1
            return True

        if win is None:
            return _fallback_input()

        try:
            curses.curs_set(1)
        except curses.error:
            return _fallback_input()

        try:
            height, width = win.getmaxyx()
            prompt = "Enter task description (ESC to cancel): "

            prompt_y = max(0, height - 3)
            input_y = max(0, height - 2)
            win.move(prompt_y, 1)
            win.clrtoeol()
            win.addstr(prompt_y, 1, prompt)
            win.move(input_y, 1)
            win.clrtoeol()
            win.refresh()

            buffer: list[str] = []

            while True:
                ch = win.get_wch()
                if isinstance(ch, str):
                    if ch in ("\n", "\r"):
                        break
                    if ch == "\x1b":  # ESC
                        buffer = []
                        break
                    if ch in ("\b", "\x7f"):
                        if buffer:
                            buffer.pop()
                            y, x = win.getyx()
                            win.move(y, max(1, x - 1))
                            win.delch()
                    elif 32 <= ord(ch) <= 126:
                        buffer.append(ch)
                        win.addstr(ch)
                elif ch == curses.KEY_BACKSPACE and buffer:
                    buffer.pop()
                    y, x = win.getyx()
                    win.move(y, max(1, x - 1))
                    win.delch()

            description = "".join(buffer).strip()
            win.move(prompt_y, 0)
            win.clrtoeol()
            win.move(input_y, 0)
            win.clrtoeol()
            curses.curs_set(0)
            win.refresh()

            if not description:
                return False

            self.agent_manager.add_task(description)
            self.selected_index = len(self.agent_manager.tasks) - 1
            return True
        except Exception:
            try:
                curses.curs_set(0)
            except curses.error:
                pass
            return _fallback_input()
