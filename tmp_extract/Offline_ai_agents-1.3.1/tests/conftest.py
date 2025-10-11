from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Callable, Dict, List, Optional

import pytest
from agent_cli.models import AgentStatus
from agent_cli.theme import ThemeManager


class FakeScreen:
    """Lightweight stand-in for a curses screen used in tests."""

    def __init__(self, height: int = 24, width: int = 80) -> None:
        self.height = height
        self.width = width
        self.render_calls: List[tuple[int, int, str]] = []
        self.attrs_calls: List[tuple[int, int, str, int]] = []
        self._cleared = False
        self._refreshed = False
        self._nodelay = False
        self._keypad = False

    def getmaxyx(self) -> tuple[int, int]:
        return self.height, self.width

    def clear(self) -> None:
        self.render_calls.clear()
        self.attrs_calls.clear()
        self._cleared = True

    def erase(self) -> None:
        self.clear()

    def nodelay(self, flag: bool) -> None:
        self._nodelay = flag

    def keypad(self, flag: bool) -> None:
        self._keypad = flag

    def addstr(self, y: int, x: int, text: str, attr: Optional[int] = None) -> None:
        if attr is None:
            self.render_calls.append((y, x, text))
        else:
            self.attrs_calls.append((y, x, text, attr))

    def refresh(self) -> None:
        self._refreshed = True

    def contains(self, text: str) -> bool:
        return any(text in rendered for _, _, rendered in self.render_calls)

    def rendered_lines(self) -> List[str]:
        ordered: Dict[int, List[tuple[int, str]]] = defaultdict(list)
        for y, x, text in self.render_calls:
            ordered[y].append((x, text))
        lines: List[str] = []
        for y in sorted(ordered):
            segments = sorted(ordered[y], key=lambda item: item[0])
            line = "".join(segment for _, segment in segments)
            lines.append(line)
        return lines


class StubAgentController:
    """Test double mimicking the public surface of the real controller."""

    def __init__(self, status: Optional[AgentStatus] = None) -> None:
        self.status = status or AgentStatus(
            lifecycle_state="idle",
            cycle=0,
            active_task="",
            progress=0.0,
            message="Ready",
            is_connected=True,
            updated_at=datetime.now(),
        )
        self.status_listeners: List[Callable[[AgentStatus], None]] = []
        self.status_queue: asyncio.Queue[AgentStatus] = asyncio.Queue()
        self.thought_queue: asyncio.Queue = asyncio.Queue()
        self.log_queue: asyncio.Queue = asyncio.Queue()

    def subscribe_status(self, callback: Callable[[AgentStatus], None]) -> None:
        self.status_listeners.append(callback)

    def push_status(self, status: AgentStatus) -> None:
        self.status = status
        self.status_queue.put_nowait(status)
        for callback in list(self.status_listeners):
            callback(status)

    async def start(self) -> None:  # pragma: no cover - async stub
        raise RuntimeError("StubAgentController.start should not be awaited in tests")


class StubInteraction:
    """Deterministic interaction provider for panel tests."""

    def __init__(self) -> None:
        self.prompt_queue: List[str | None] = []
        self.prompt_history: List[tuple[str, str, str]] = []
        self.confirm_queue: List[bool] = []
        self.confirm_history: List[str] = []
        self.notifications: List[str] = []

    def queue_prompt(self, response: str | None) -> None:
        self.prompt_queue.append(response)

    def queue_confirm(self, response: bool) -> None:
        self.confirm_queue.append(response)

    def prompt_text(self, prompt: str, *, default: str = "", title: str = "") -> Optional[str]:
        self.prompt_history.append((prompt, default, title))
        if self.prompt_queue:
            return self.prompt_queue.pop(0)
        return None

    def confirm(self, message: str) -> bool:
        self.confirm_history.append(message)
        if self.confirm_queue:
            return self.confirm_queue.pop(0)
        return False

    def notify(self, message: str) -> None:
        self.notifications.append(message)


@pytest.fixture()
def fake_screen() -> FakeScreen:
    return FakeScreen()


@pytest.fixture()
def theme_manager() -> ThemeManager:
    return ThemeManager()


@pytest.fixture()
def stub_agent_controller() -> StubAgentController:
    return StubAgentController()


@pytest.fixture()
def stub_interaction() -> StubInteraction:
    return StubInteraction()
