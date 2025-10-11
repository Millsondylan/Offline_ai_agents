"""Panels exposed by the compatibility dashboard."""

from .base import Panel
from .code_editor import CodeEditorPanel
from .help import HelpPanel
from .home import HomePanel
from .logs import LogsPanel
from .model_config import ModelConfigPanel
from .task_manager import TaskManagerPanel
from .thinking import ThinkingPanel
from .verification import VerificationPanel

__all__ = [
    "Panel",
    "HomePanel",
    "TaskManagerPanel",
    "ThinkingPanel",
    "LogsPanel",
    "CodeEditorPanel",
    "ModelConfigPanel",
    "HelpPanel",
    "VerificationPanel",
]

