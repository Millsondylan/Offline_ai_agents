"""Terminal prompt helpers for curses panels."""

from __future__ import annotations

from typing import Callable, Optional


class InteractionProvider:
    """Provide blocking stdin prompts, suspending curses while awaiting input."""

    def __init__(
        self,
        *,
        suspend: Optional[Callable[[], None]] = None,
        resume: Optional[Callable[[], None]] = None,
    ) -> None:
        self._suspend = suspend
        self._resume = resume

    def prompt_text(self, prompt: str, *, default: str = "", title: str = "") -> Optional[str]:
        self._before_prompt()
        try:
            message = f"{title + ': ' if title else ''}{prompt}"
            suffix = f" [{default}]" if default else ""
            text = input(f"{message}{suffix}: ")
        except (EOFError, KeyboardInterrupt):
            return None
        finally:
            self._after_prompt()
        text = text.strip()
        if not text and default:
            return default
        return text or None

    def confirm(self, message: str, default: bool = False) -> bool:
        suffix = "[Y/n]" if default else "[y/N]"
        self._before_prompt()
        try:
            text = input(f"{message} {suffix} ")
        except (EOFError, KeyboardInterrupt):
            return False
        finally:
            self._after_prompt()
        text = text.strip().lower()
        if not text:
            return default
        return text in {"y", "yes"}

    def notify(self, message: str) -> None:
        self._before_prompt()
        try:
            print(message)
        finally:
            self._after_prompt()

    def _before_prompt(self) -> None:
        if self._suspend:
            self._suspend()

    def _after_prompt(self) -> None:
        if self._resume:
            self._resume()


__all__ = ["InteractionProvider"]
