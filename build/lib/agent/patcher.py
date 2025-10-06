import os
import re
import subprocess
import tempfile
from typing import Optional


ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
FENCE_LABELED_RE = re.compile(r"```(?:diff|patch)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
FENCE_ANY_RE = re.compile(r"```[a-zA-Z0-9_+.-]*\s*\n(.*?)\n```", re.DOTALL)


def strip_ansi(s: str) -> str:
    return ANSI_ESCAPE_RE.sub("", s)


def extract_unified_diff(text: str) -> Optional[str]:
    if not text:
        return None
    clean = strip_ansi(text)

    # Prefer the last labeled fenced diff/patch block
    last = None
    for m in FENCE_LABELED_RE.finditer(clean):
        body = m.group(1).strip()
        if looks_like_unified_diff(body):
            last = body
    if last:
        return last

    # Next, any fenced block that contains diff markers
    for m in FENCE_ANY_RE.finditer(clean):
        body = m.group(1).strip()
        if looks_like_unified_diff(body):
            last = body
    if last:
        return last

    # If there's a git-style diff in the stream, slice from first occurrence
    idx = clean.find("diff --git ")
    if idx != -1:
        return clean[idx:].strip()

    # Fallback to raw if it looks like a diff
    if looks_like_unified_diff(clean):
        return clean

    return None


def looks_like_unified_diff(s: str) -> bool:
    return any(h in s for h in ("--- ", "+++ ", "@@ "))


def _rewrite_patch_paths(patch_text: str, prefix: str) -> str:
    if not prefix:
        return patch_text
    lines = []
    for line in patch_text.splitlines():
        if line.startswith('diff --git a/') and ' b/' in line:
            parts = line.split(' ')
            try:
                a_idx = parts.index('a/' + parts[3].split('a/')[1])
            except Exception:
                a_idx = None
            # Simpler: rebuild using split
            before, after = line.split(' a/', 1)
            left, right = after.split(' b/', 1)
            line = f"{before} a/{prefix}{left} b/{prefix}{right}"
        elif line.startswith('--- a/'):
            line = '--- a/' + prefix + line[6:]
        elif line.startswith('+++ b/'):
            line = '+++ b/' + prefix + line[6:]
        lines.append(line)
    return '\n'.join(lines) + ('\n' if not patch_text.endswith('\n') else '')


from typing import Optional


def apply_patch_with_git(repo_root: str, patch_text: str, work_dir: str, path_prefix: Optional[str] = None) -> str:
    """
    Writes a temporary patch file and runs `git apply`.
    Returns combined stdout/stderr for logging.
    """
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".patch") as tf:
        if path_prefix:
            patched = _rewrite_patch_paths(patch_text, path_prefix)
        else:
            patched = patch_text
        tf.write(patched)
        tmp_path = tf.name

    try:
        proc = subprocess.run(
            ["git", "apply", "-v", "--reject", "--whitespace=fix", tmp_path],
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        out = proc.stdout.decode("utf-8", errors="replace")
        return out
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
