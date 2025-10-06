"""Theme management utilities for the control panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Theme:
    """Color palette description."""

    name: str
    accents: Dict[str, int]
    text: Dict[str, int]
    background: int


class ThemeManager:
    """Manage dark/light themes with monochrome fallback."""

    def __init__(self) -> None:
        self._themes: Dict[str, Theme] = {
            "dark": Theme(
                name="dark",
                accents={
                    "header": 1,
                    "sidebar": 2,
                    "footer": 3,
                    "highlight": 4,
                    "error": 5,
                },
                text={
                    "primary": 6,
                    "muted": 7,
                    "faded": 8,
                },
                background=0,
            ),
            "light": Theme(
                name="light",
                accents={
                    "header": 11,
                    "sidebar": 12,
                    "footer": 13,
                    "highlight": 14,
                    "error": 15,
                },
                text={
                    "primary": 16,
                    "muted": 17,
                    "faded": 18,
                },
                background=10,
            ),
        }
        self._active = "dark"
        self._monochrome = False

    @property
    def active_theme(self) -> str:
        return self._themes[self._active].name

    def toggle(self) -> None:
        self._active = "light" if self._active == "dark" else "dark"

    def toggle_theme(self) -> None:
        self.toggle()

    def get_color(self, token: str) -> int:
        if self._monochrome:
            return 0
        palette = self._themes[self._active]
        if token in palette.accents:
            return palette.accents[token]
        return palette.text.get(token, palette.background)

    def set_theme(self, name: str) -> None:
        if name not in self._themes:
            raise ValueError(f"Unknown theme '{name}'")
        self._active = name

    def configure_monochrome(self, monochrome: bool) -> None:
        self._monochrome = monochrome

    def is_monochrome(self) -> bool:
        return self._monochrome

    def theme_data(self) -> Theme:
        return self._themes[self._active]

    def palette_for(self, name: str) -> Theme:
        if name not in self._themes:
            raise ValueError(f"Unknown theme '{name}'")
        return self._themes[name]


__all__ = ["Theme", "ThemeManager"]
