from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from .base import Provider


class ManualProvider(Provider):
    """Human-in-the-loop provider that waits for patches dropped in the inbox."""

    name = "manual"
    mode = "offline"

    def __init__(self, config: Optional[Dict] = None) -> None:
        super().__init__(config)
        repo_root = Path(__file__).resolve().parents[2]
        self.global_inbox = repo_root / "agent" / "inbox"
        self.inbox_filename = self.config.get("filename", "inbox.patch")

    def generate_patch(self, prompt: str, cycle_dir: str) -> Optional[str]:
        os.makedirs(cycle_dir, exist_ok=True)
        prompt_path = os.path.join(cycle_dir, "prompt.md")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt)

        patch_path = os.path.join(cycle_dir, self.inbox_filename)
        if os.path.exists(patch_path):
            return self._read(patch_path)

        base = os.path.basename(cycle_dir.rstrip(os.sep))
        global_patch = self.global_inbox / f"{base}.patch"
        if global_patch.exists():
            return self._read(global_patch)
        return None

    @staticmethod
    def _read(path: Path | str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
