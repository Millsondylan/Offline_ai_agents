"""Modern Codex-style dashboard using Textual framework."""

import sys
import asyncio
from pathlib import Path
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Footer, Static
from textual.binding import Binding

from agent_dashboard.core.real_agent_manager import RealAgentManager
from agent_dashboard.codex_widgets import (
    StatusHeader,
    NavSidebar,
    MetricsSidebar,
    ThinkingStream,
    TaskPanel,
    LogViewer,
    CodeViewer,
    ModelConfigPanel,
    ProjectGoalPanel,
)


class CodexDashboard(App):
    """Modern Codex-style AI Agent Dashboard."""

    CSS = """
    /* Global theme colors - Codex inspired dark theme */
    * {
        scrollbar-background: $panel;
        scrollbar-color: $primary;
        scrollbar-color-hover: $accent;
        scrollbar-color-active: $success;
    }

    Screen {
        background: $background;
    }

    /* Main content area */
    #content-area {
        height: 1fr;
        background: $surface;
    }

    /* Footer styling */
    Footer {
        background: $panel;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("1", "show_tasks", "Tasks"),
        Binding("2", "show_thinking", "Thinking"),
        Binding("3", "show_logs", "Logs"),
        Binding("4", "show_code", "Code"),
        Binding("5", "show_model", "Model"),
        Binding("6", "show_goal", "Goal"),
        Binding("g", "show_goal", "Goal"),
        Binding("s", "start_agent", "Start"),
        Binding("p", "pause_agent", "Pause"),
        Binding("x", "stop_agent", "Stop"),
        Binding("r", "run_verification", "Verify"),
    ]

    def __init__(self):
        super().__init__()
        self.title = "AI Agent Dashboard - Codex Edition"
        self.sub_title = "Modern autonomous AI agent monitoring"
        self.dark = True

        self._agent_manager = RealAgentManager()
        self._current_panel = "tasks"
        self._update_interval = 0.1
        self._is_updating = False

    def get_css_variables(self) -> dict[str, str]:
        """Define custom theme colors for Codex-style dark theme."""
        variables = super().get_css_variables()
        variables.update({
            "background": "#0A0E27",
            "surface": "#0D1117",
            "panel": "#161B22",
            "boost": "#1F2937",
            "primary": "#30363D",
            "accent": "#58A6FF",
            "success": "#3FB950",
            "warning": "#D29922",
            "error": "#F85149",
            "text": "#C9D1D9",
            "text-muted": "#8B949E",
        })
        return variables

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        yield StatusHeader()
        yield NavSidebar()
        yield MetricsSidebar()

        with Container(id="content-area"):
            yield TaskPanel(id="panel-tasks")
            yield ThinkingStream(id="panel-thinking")
            yield LogViewer(id="panel-logs")
            yield CodeViewer(id="panel-code")
            yield ModelConfigPanel(id="panel-model")
            yield ProjectGoalPanel(id="panel-goal")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize dashboard when mounted."""
        self._show_panel(self._current_panel)
        self._start_updates()

    def _show_panel(self, panel_name: str) -> None:
        """Show the selected panel and hide others."""
        self._current_panel = panel_name

        panels = {
            "tasks": "panel-tasks",
            "thinking": "panel-thinking",
            "logs": "panel-logs",
            "code": "panel-code",
            "model": "panel-model",
            "goal": "panel-goal",
        }

        for name, panel_id in panels.items():
            try:
                panel = self.query_one(f"#{panel_id}")
                if name == panel_name:
                    panel.display = True
                else:
                    panel.display = False
            except Exception:
                pass

        try:
            nav = self.query_one(NavSidebar)
            nav.set_active_panel(panel_name)
        except Exception:
            pass

    @work(exclusive=True)
    async def _start_updates(self) -> None:
        """Start the update loop for live data."""
        self._is_updating = True

        while self._is_updating:
            await self._update_dashboard()
            await asyncio.sleep(self._update_interval)

    async def _update_dashboard(self) -> None:
        """Update all dashboard components with latest data."""
        try:
            state = self._agent_manager.get_state()
            tasks = self._agent_manager.tasks
            logs = self._agent_manager.get_logs()

            try:
                header = self.query_one(StatusHeader)
                header.update_state(state)
            except Exception:
                pass

            try:
                metrics = self.query_one(MetricsSidebar)
                metrics.update_metrics(state, tasks)
            except Exception:
                pass

            if self._current_panel == "tasks":
                try:
                    task_panel = self.query_one("#panel-tasks", TaskPanel)
                    task_panel.update_tasks(tasks)
                except Exception:
                    pass

            elif self._current_panel == "thinking":
                try:
                    thinking_stream = self.query_one("#panel-thinking", ThinkingStream)
                    thinking_stream.update_stream()
                except Exception:
                    pass

            elif self._current_panel == "logs":
                try:
                    log_viewer = self.query_one("#panel-logs", LogViewer)
                    log_viewer.update_logs(logs)
                except Exception:
                    pass

            elif self._current_panel == "goal":
                try:
                    goal_panel = self.query_one("#panel-goal", ProjectGoalPanel)
                    # Update progress
                    total = len(tasks)
                    completed = sum(1 for t in tasks if t.status.value == "Completed")
                    goal_panel.update_progress(total, completed)
                except Exception:
                    pass

        except Exception:
            pass

    def on_nav_sidebar_panel_selected(self, message: NavSidebar.PanelSelected) -> None:
        """Handle panel selection from navigation sidebar."""
        self._show_panel(message.panel_name)

    def on_nav_sidebar_control_action(self, message: NavSidebar.ControlAction) -> None:
        """Handle control actions from navigation sidebar."""
        action = message.action

        if action == "start":
            self._start_agent()
        elif action == "pause":
            self._pause_agent()
        elif action == "stop":
            self._stop_agent()
        elif action == "verify":
            self._run_verification()

    def on_nav_sidebar_system_action(self, message: NavSidebar.SystemAction) -> None:
        """Handle system actions from navigation sidebar."""
        action = message.action

        if action == "model":
            self.notify("Model configuration not yet implemented", severity="information")
        elif action == "exit":
            self.exit()

    def on_task_panel_task_added(self, message: TaskPanel.TaskAdded) -> None:
        """Handle task addition."""
        try:
            self._agent_manager.add_task(message.description)
            self.notify(f"Task added: {message.description[:50]}", severity="information")
        except Exception as e:
            self.notify(f"Error adding task: {str(e)}", severity="error")

    def on_task_panel_task_activated(self, message: TaskPanel.TaskActivated) -> None:
        """Handle task activation."""
        try:
            self._agent_manager.set_active_task(message.task_id)
            self.notify(f"Task #{message.task_id} activated", severity="information")
        except Exception as e:
            self.notify(f"Error activating task: {str(e)}", severity="error")

    def on_task_panel_task_deleted(self, message: TaskPanel.TaskDeleted) -> None:
        """Handle task deletion."""
        try:
            self._agent_manager.delete_task(message.task_id)
            self.notify(f"Task #{message.task_id} deleted", severity="information")
        except Exception as e:
            self.notify(f"Error deleting task: {str(e)}", severity="error")

    def on_task_panel_refresh_requested(self, message: TaskPanel.RefreshRequested) -> None:
        """Handle refresh request."""
        self.notify("Refreshing tasks...", severity="information")

    def on_project_goal_panel_generate_tasks_requested(self, message: ProjectGoalPanel.GenerateTasksRequested) -> None:
        """Handle task generation request from project goal panel."""
        try:
            self.notify(f"Generating tasks for: {message.project_title}", severity="information")

            # Use AI to generate tasks
            generated_tasks = self._agent_manager.generate_tasks_from_goal(message.objective)

            # Notify the panel of completion
            try:
                goal_panel = self.query_one("#panel-goal", ProjectGoalPanel)
                goal_panel.task_generation_complete(len(generated_tasks), len(generated_tasks) > 0)
            except Exception:
                pass

            if generated_tasks:
                self.notify(f"Successfully generated {len(generated_tasks)} tasks!", severity="information")
            else:
                self.notify("Failed to generate tasks", severity="error")

        except Exception as e:
            self.notify(f"Error generating tasks: {str(e)}", severity="error")
            try:
                goal_panel = self.query_one("#panel-goal", ProjectGoalPanel)
                goal_panel.task_generation_complete(0, False)
            except Exception:
                pass

    def on_project_goal_panel_start_project_requested(self, message: ProjectGoalPanel.StartProjectRequested) -> None:
        """Handle project start request."""
        try:
            # Activate the first pending task if any
            pending_tasks = [t for t in self._agent_manager.tasks if t.status.value == "Pending"]
            if pending_tasks:
                first_task = pending_tasks[0]
                self._agent_manager.set_active_task(first_task.id)
                self.notify(f"Activated task: {first_task.description[:50]}", severity="information")

            # Start the agent
            self._start_agent()

        except Exception as e:
            self.notify(f"Error starting project: {str(e)}", severity="error")

    def on_project_goal_panel_refresh_progress_requested(self, message: ProjectGoalPanel.RefreshProgressRequested) -> None:
        """Handle progress refresh request."""
        try:
            tasks = self._agent_manager.tasks
            goal_panel = self.query_one("#panel-goal", ProjectGoalPanel)
            total = len(tasks)
            completed = sum(1 for t in tasks if t.status.value == "Completed")
            goal_panel.update_progress(total, completed)
            self.notify(f"Progress: {completed}/{total} tasks complete", severity="information")
        except Exception as e:
            self.notify(f"Error refreshing progress: {str(e)}", severity="error")

    def _start_agent(self) -> None:
        """Start the agent."""
        try:
            self._agent_manager.start()
            self.notify("Agent started", severity="information")
        except Exception as e:
            self.notify(f"Error starting agent: {str(e)}", severity="error")

    def _pause_agent(self) -> None:
        """Pause the agent."""
        try:
            self._agent_manager.pause()
            self.notify("Agent paused", severity="information")
        except Exception as e:
            self.notify(f"Error pausing agent: {str(e)}", severity="error")

    def _stop_agent(self) -> None:
        """Stop the agent."""
        try:
            self._agent_manager.stop()
            self.notify("Agent stopped", severity="information")
        except Exception as e:
            self.notify(f"Error stopping agent: {str(e)}", severity="error")

    def _run_verification(self) -> None:
        """Run verification tests."""
        try:
            self._agent_manager.run_verification()
            self.notify("Verification started", severity="information")
        except Exception as e:
            self.notify(f"Error running verification: {str(e)}", severity="error")

    def action_show_tasks(self) -> None:
        """Show tasks panel."""
        self._show_panel("tasks")

    def action_show_thinking(self) -> None:
        """Show thinking stream panel."""
        self._show_panel("thinking")

    def action_show_logs(self) -> None:
        """Show logs panel."""
        self._show_panel("logs")

    def action_show_code(self) -> None:
        """Show code viewer panel."""
        self._show_panel("code")

    def action_show_model(self) -> None:
        """Show model config panel."""
        self._show_panel("model")

    def action_show_goal(self) -> None:
        """Show project goal panel."""
        self._show_panel("goal")

    def action_start_agent(self) -> None:
        """Start agent via keyboard shortcut."""
        self._start_agent()

    def action_pause_agent(self) -> None:
        """Pause agent via keyboard shortcut."""
        self._pause_agent()

    def action_stop_agent(self) -> None:
        """Stop agent via keyboard shortcut."""
        self._stop_agent()

    def action_run_verification(self) -> None:
        """Run verification via keyboard shortcut."""
        self._run_verification()

    def action_quit(self) -> None:
        """Quit the application."""
        self._is_updating = False
        self._agent_manager.stop()
        self.exit()


def run_codex_dashboard() -> None:
    """Entry point to run the Codex dashboard."""
    try:
        app = CodexDashboard()
        app.run()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error running Codex dashboard: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_codex_dashboard()
