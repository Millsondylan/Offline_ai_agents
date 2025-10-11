"""Terminal UI compatibility layer used by the test-suite."""

from .app import AgentTUI
from .navigation import NavEntry, NavigationManager
from .state_watcher import StateWatcher

__all__ = ["AgentTUI", "NavigationManager", "NavEntry", "StateWatcher"]

