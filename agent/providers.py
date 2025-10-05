import os
import subprocess
from typing import Optional, List


class Provider:
    def generate_patch(self, prompt: str, cycle_dir: str) -> Optional[str]:
        raise NotImplementedError


class ManualProvider(Provider):
    """
    Writes prompt to disk and waits for a human to place a patch file.
    Patch file path: {cycle_dir}/inbox.patch
    """

    def __init__(self) -> None:
        pass

    def generate_patch(self, prompt: str, cycle_dir: str) -> Optional[str]:
        prompt_path = os.path.join(cycle_dir, "prompt.md")
        os.makedirs(cycle_dir, exist_ok=True)
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt)

        inbox_patch = os.path.join(cycle_dir, "inbox.patch")
        # No blocking wait here; the runner will check later.
        if os.path.exists(inbox_patch):
            with open(inbox_patch, "r", encoding="utf-8") as f:
                return f.read()

        # Also support global inbox path: agent/inbox/<cycle_basename>.patch
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        base = os.path.basename(cycle_dir)
        global_patch = os.path.join(root, "agent", "inbox", f"{base}.patch")
        if os.path.exists(global_patch):
            with open(global_patch, "r", encoding="utf-8") as f:
                return f.read()
        return None


class CommandProvider(Provider):
    """
    Runs a shell command with the prompt on stdin and returns stdout as text.
    Config example: cmd = ["bash", "-lc", "ollama run llama3:latest"]
    """

    def __init__(self, cmd: List[str], timeout_seconds: int = 600) -> None:
        self.cmd = cmd
        self.timeout_seconds = timeout_seconds

    def generate_patch(self, prompt: str, cycle_dir: str) -> Optional[str]:
        # Persist prompt for inspection even when using a command-based provider
        os.makedirs(cycle_dir, exist_ok=True)
        with open(os.path.join(cycle_dir, "prompt.md"), "w", encoding="utf-8") as f:
            f.write(prompt)
        if not self.cmd:
            return None
        try:
            proc = subprocess.run(
                self.cmd,
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=self.timeout_seconds,
            )
            out = proc.stdout.decode("utf-8", errors="replace")
            # Save raw output for inspection
            with open(os.path.join(cycle_dir, "provider_output.txt"), "w", encoding="utf-8") as f:
                f.write(out)
            return out
        except subprocess.TimeoutExpired:
            return None
