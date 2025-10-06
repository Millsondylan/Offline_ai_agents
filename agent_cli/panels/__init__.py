"""Panel exports for the control panel."""

from agent_cli.panels.base import Panel, PanelContext
from agent_cli.panels.code_editor import CodeEditorPanel
from agent_cli.panels.help import HelpPanel
from agent_cli.panels.home import HomePanel
from agent_cli.panels.logs import LogsPanel
from agent_cli.panels.model_config import ModelConfigPanel
from agent_cli.panels.task_manager import TaskManagerPanel
from agent_cli.panels.thinking import ThinkingPanel
from agent_cli.panels.verification import VerificationPanel

__all__ = [
    "Panel",
    "PanelContext",
    "CodeEditorPanel",
    "HelpPanel",
    "HomePanel",
    "TaskManagerPanel",
    "ThinkingPanel",
    "LogsPanel",
    "ModelConfigPanel",
    "VerificationPanel",
]
