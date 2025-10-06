"""Application glue for the agent CLI control panel."""

from __future__ import annotations

import asyncio
import curses
from pathlib import Path
from typing import List

from agent_cli.agent_controller import AgentController
from agent_cli.interaction import InteractionProvider
from agent_cli.panels.code_editor import CodeEditorPanel
from agent_cli.panels.help import HelpPanel
from agent_cli.panels.home import HomePanel
from agent_cli.panels.logs import LogsPanel
from agent_cli.panels.model_config import ModelConfigPanel
from agent_cli.panels.task_manager import TaskManagerPanel
from agent_cli.panels.thinking import ThinkingPanel
from agent_cli.panels.verification import VerificationPanel
from agent_cli.state_manager import StateManager
from agent_cli.state_sync import StateSynchronizer
from agent_cli.theme import ThemeManager
from agent_cli.ui_manager import UIManager
from agent.tui.state_watcher import StateWatcher


async def run_agent_listener(controller: AgentController, ui: UIManager) -> None:
    """Stream controller status queue into the UI."""
    while True:
        status = await controller.status_queue.get()
        ui.update_status(status)


async def run_thought_listener(controller: AgentController, panel: ThinkingPanel, ui: UIManager) -> None:
    while True:
        thought = await controller.thought_queue.get()
        panel.add_thought(thought)
        ui.render()


async def run_logs_listener(controller: AgentController, panel: LogsPanel, ui: UIManager) -> None:
    while True:
        log = await controller.log_queue.get()
        panel.add_log(log)
        ui.render()


async def draw_loop(ui: UIManager) -> None:
    while True:
        await asyncio.sleep(0.1)
        ui.render()


async def main_async(stdscr, control_dir: Path, project_root: Path) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    interaction = InteractionProvider(
        suspend=lambda: curses.endwin(),
        resume=lambda: stdscr.refresh(),
    )
    controller = AgentController(control_dir=control_dir)
    state_manager = StateManager(base_path=Path.home() / ".agent_cli")
    theme_manager = ThemeManager()

    panels = [
        HomePanel(),
        TaskManagerPanel(interaction=interaction),
        ThinkingPanel(),
        LogsPanel(interaction=interaction),
        CodeEditorPanel(root_path=project_root, interaction=interaction),
        ModelConfigPanel(config_path=Path.home() / ".agent_cli" / "model_config.json"),
        VerificationPanel(results_path=Path.home() / ".agent_cli" / "test_results.json"),
        HelpPanel(interaction=interaction),
    ]

    ui = UIManager(
        screen=stdscr,
        agent_controller=controller,
        panels=panels,
        theme_manager=theme_manager,
        state_manager=state_manager,
    )

    watcher = StateSynchronizer(
        watcher=StateWatcher(),
        ui=ui,
        home_panel=panels[0],
        thinking_panel=panels[2],
        logs_panel=panels[3],
    )

    tasks = [
        asyncio.create_task(draw_loop(ui)),
        asyncio.create_task(watcher.run()),
    ]

    try:
        while True:
            key = stdscr.getch()
            if key == -1:
                await asyncio.sleep(0.05)
                continue
            handled = ui.handle_key(key)
            if not handled:
                ui.render()
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def main(control_dir: Path | None = None, project_root: Path | None = None) -> None:
    control_dir = control_dir or Path.home() / ".agent_cli" / "control"
    project_root = project_root or Path.cwd()

    def wrapped(stdscr):
        asyncio.run(main_async(stdscr, control_dir=control_dir, project_root=project_root))

    curses.wrapper(wrapped)


__all__ = [
    "main",
    "run_agent_listener",
    "run_thought_listener",
    "run_logs_listener",
]
