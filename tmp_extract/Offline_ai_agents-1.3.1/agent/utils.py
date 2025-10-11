import os
import shutil
import subprocess
import time
from glob import glob
from typing import Optional, Tuple


def now_ts() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def run_cmd(cmd: str, timeout: int = 600) -> Tuple[int, str]:
    print(f"Running command: {cmd}")
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            executable="/bin/bash",
        )
        out = proc.stdout.decode("utf-8", errors="replace")
        return proc.returncode, out
    except subprocess.TimeoutExpired:
        return 124, f"[timeout after {timeout}s] {cmd}"


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def write_text(path: str, content: str) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def read_text(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def collect_artifacts(pattern: str, dest_dir: str) -> int:
    count = 0
    for src in glob(pattern, recursive=True):
        if os.path.isfile(src):
            rel = os.path.basename(src)
            dst = os.path.join(dest_dir, rel)
            ensure_dir(dest_dir)
            shutil.copy2(src, dst)
            count += 1
    return count

