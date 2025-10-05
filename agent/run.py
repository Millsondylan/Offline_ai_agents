import json
import os
import time
from typing import Dict, Any, List, Optional, Tuple

from .providers import ManualProvider, CommandProvider
from .utils import now_ts, run_cmd, ensure_dir, write_text, read_text, collect_artifacts
import re
from .patcher import extract_unified_diff, apply_patch_with_git
from .analyzers.base import AnalyzerResult
from .analyzers.ruff import RuffAnalyzer
from .analyzers.pytest_cov import PytestCoverageAnalyzer
from .analyzers.bandit import BanditAnalyzer
from .analyzers.semgrep import SemgrepAnalyzer
from .analyzers.pip_audit import PipAuditAnalyzer
from .analyzers.repo_hygiene import RepoHygieneAnalyzer


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _collect_error_files(repo_root: str, logs: str, limit: int = 5) -> Dict[str, str]:
    files: Dict[str, str] = {}
    if not logs:
        return files
    candidates = []
    for m in re.finditer(r"\b(lib/[\w\-/]+\.dart)", logs):
        candidates.append(m.group(1))
    for path in candidates:
        if path in files:
            continue
        abs_path = os.path.join(repo_root, "insightflow_ai_trading", path)
        if os.path.exists(abs_path):
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                files[path] = content[:20000]
            except Exception:
                pass
        if len(files) >= limit:
            break
    return files


def compose_prompt(repo_root: str, cycle_dir: str, results: Dict[str, Any]) -> str:
    parts = []
    parts.append("Agent Cycle Prompt\n")
    parts.append("Context:\n")
    # Git status and changed files
    code, out = run_cmd("git status --porcelain=v1 && echo --- && git rev-parse --abbrev-ref HEAD && echo --- && git log -1 --oneline", timeout=15)
    parts.append("[git]\n" + out.strip() + "\n")

    # Command outputs
    for key, r in results.items():
        parts.append(f"[command:{key}] exit={r['code']}\n")
        parts.append(r["output"][:20000] + ("\n" if not r["output"].endswith("\n") else ""))

    # Include likely-problem files based on errors
    combined_logs = "\n".join([r.get("output", "") or "" for r in results.values()])
    file_map = _collect_error_files(repo_root, combined_logs)
    if file_map:
        parts.append("\nFiles:\n")
        for rel, content in file_map.items():
            parts.append(f"[file:{rel}]\n{content}\n")

    parts.append("\nTask:\n")
    parts.append(
        "You are an automated code-fixing agent. Propose the smallest safe patch to make tests pass or address clear issues discovered in analyze/test logs, limiting changes to files shown in [Files] and related imports. "
        "Rules: 1) Keep diffs minimal and compilable. 2) Only touch necessary files. 3) Include complete content for any new files. 4) No explanations, no prose. 5) Do not include binary files."
    )
    parts.append("\nOutput format:\n")
    parts.append(
        "Return ONLY a unified diff (git-style) in a fenced block:```diff\n<diff>\n```\n"
        "Do not add commentary or non-diff text."
    )
    return "\n".join(parts)


def _parse_files_from_diff(patch_text: str):
    files = []
    if not patch_text:
        return files
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.strip().split()
            if len(parts) >= 4:
                a_path = parts[2]
                if a_path.startswith("a/"):
                    a_path = a_path[2:]
                files.append(a_path)
    # Preserve order, dedupe
    seen = set()
    ordered = []
    for f in files:
        if f not in seen:
            ordered.append(f)
            seen.add(f)
    return ordered


def _build_commit_message(repo_root: str, patch_text: str, cycle_dir: str) -> str:
    # Stage changes first to compute stats
    run_cmd("git add -A")
    _, names_out = run_cmd("git diff --cached --name-only")
    _, stat_out = run_cmd("git diff --cached --shortstat")
    names = [n.strip() for n in (names_out or "").splitlines() if n.strip()]
    summary = (stat_out or "").strip()
    if not summary:
        # Fallback to listing a few filenames
        from_diff = _parse_files_from_diff(patch_text)
        show = from_diff or names
        if show:
            base = [os.path.basename(s) for s in show[:3]]
            if len(show) > 3:
                summary = f"update {', '.join(base)}, +{len(show)-3} more"
            else:
                summary = f"update {', '.join(base)}"
        else:
            summary = "apply patch"
    first_line = f"agent edits: {summary}".strip()
    # Single-line commit subject per requirement
    return first_line + "\n"


def provider_from_config(cfg: Dict[str, Any]):
    p = cfg.get("provider", {})
    ptype = p.get("type", "manual")
    if ptype == "command":
        return CommandProvider(p.get("command", {}).get("cmd", []), p.get("command", {}).get("timeout_seconds", 600))
    return ManualProvider()


def _an_res(res: Optional[AnalyzerResult]):
    if not res:
        return {"skipped": True}
    return {
        "ok": res.ok,
        "skipped": res.skipped,
        "summary": res.summary,
    }


def _run_analyzers_and_gate(
    repo_root: str,
    cfg: Dict[str, Any],
    cycle_dir: str,
    proposed_files: Optional[List[str]] = None,
) -> Dict[str, Any]:
    gate_cfg = cfg.get("gate", {})
    semgrep_rules = gate_cfg.get("semgrep_rules", [])
    pip_fix = bool(gate_cfg.get("pip_audit_fix", False))
    min_cov = float(gate_cfg.get("min_coverage", 0.0))

    analyzers = [
        RuffAnalyzer(),
        PytestCoverageAnalyzer(),
        BanditAnalyzer(),
        SemgrepAnalyzer(),
        PipAuditAnalyzer(),
        RepoHygieneAnalyzer(),
    ]

    results: Dict[str, AnalyzerResult] = {}

    for a in analyzers:
        if isinstance(a, SemgrepAnalyzer):
            res = a.run(repo_root, cycle_dir, proposed_files, rules=semgrep_rules)
        elif isinstance(a, PipAuditAnalyzer):
            res = a.run(repo_root, cycle_dir, proposed_files, fix=pip_fix)
        else:
            res = a.run(repo_root, cycle_dir, proposed_files)
        results[a.name] = res

    allow = True
    rationale: List[str] = []

    # Ruff
    if "ruff" in results and not results["ruff"].skipped and not results["ruff"].ok:
        allow = False
        rationale.append("ruff failed: style errors present")

    # Tests + coverage
    if "pytest_cov" in results and not results["pytest_cov"].skipped:
        cov_report = results["pytest_cov"].data.get("coverage_json", {}) if results["pytest_cov"].data else {}
        cov_pct = None
        try:
            totals = cov_report.get("totals", {})
            val = totals.get("percent_covered")
            if isinstance(val, (int, float)):
                cov_pct = float(val) / 100.0
        except Exception:
            cov_pct = None
        if not results["pytest_cov"].ok:
            allow = False
            rationale.append("pytest failed")
        elif cov_pct is not None and cov_pct < min_cov:
            allow = False
            rationale.append(f"coverage below threshold: {cov_pct:.2%} < {min_cov:.2%}")

    # Bandit
    if "bandit" in results and not results["bandit"].skipped and not results["bandit"].ok:
        allow = False
        rationale.append("bandit high/critical issues present")

    # Semgrep
    if "semgrep" in results and not results["semgrep"].skipped and not results["semgrep"].ok:
        allow = False
        rationale.append("semgrep findings present")

    # pip-audit
    if "pip_audit" in results and not results["pip_audit"].skipped and not results["pip_audit"].ok:
        allow = False
        rationale.append("pip-audit vulnerabilities present")

    pg = {
        "allow": allow,
        "rationale": rationale,
        "ruff": _an_res(results.get("ruff")),
        "pytest_cov": _an_res(results.get("pytest_cov")),
        "bandit": _an_res(results.get("bandit")),
        "semgrep": _an_res(results.get("semgrep")),
        "pip_audit": _an_res(results.get("pip_audit")),
        "repo_hygiene": _an_res(results.get("repo_hygiene")),
    }
    write_text(os.path.join(cycle_dir, "production_gate.json"), json.dumps(pg, indent=2))
    return pg


def subprocess_with_env(args: List[str], cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
    import subprocess as _sp
    proc = _sp.run(args, cwd=cwd, env=env, stdout=_sp.PIPE, stderr=_sp.STDOUT, check=False)
    return proc.returncode, proc.stdout.decode("utf-8", errors="replace")


def _commit_with_temp_index(
    repo_root: str,
    branch: Optional[str],
    msg: str,
    proposed_files: List[str],
    cycle_dir: str,
) -> Tuple[bool, Dict[str, Any]]:
    meta: Dict[str, Any] = {}
    tmp_index = os.path.join(cycle_dir, "_tmp_index")
    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = tmp_index

    # Baseline
    code, out = subprocess_with_env(["git", "rev-parse", "HEAD"], cwd=repo_root, env=env)
    if code != 0:
        meta["error"] = "rev-parse HEAD failed"
        write_text(os.path.join(cycle_dir, "commit.meta.json"), json.dumps(meta, indent=2))
        return False, meta
    head = (out or "").strip().splitlines()[-1]

    # Ensure branch exists
    if branch:
        run_cmd(f"git rev-parse --verify {branch} >/dev/null 2>&1 || git checkout -B {branch}")
        run_cmd(f"git checkout {branch}")

    # Load tree into temp index
    code, out = subprocess_with_env(["git", "read-tree", head], cwd=repo_root, env=env)
    meta["read-tree"] = {"code": code, "out": out}
    if code != 0:
        write_text(os.path.join(cycle_dir, "commit.meta.json"), json.dumps(meta, indent=2))
        return False, meta

    # Stage only proposed files
    for p in proposed_files:
        subprocess_with_env(["git", "add", "--", p], cwd=repo_root, env=env)
    code, out = subprocess_with_env(["git", "diff", "--cached", "--name-only"], cwd=repo_root, env=env)
    staged = [ln.strip() for ln in (out or "").splitlines() if ln.strip()]
    extra = [p for p in staged if p not in proposed_files]
    meta["staged"] = staged
    meta["proposed_files"] = proposed_files
    if extra:
        meta["error"] = "staged files outside proposed patch"
        write_text(os.path.join(cycle_dir, "commit.meta.json"), json.dumps(meta, indent=2))
        return False, meta

    # Write tree
    code, out = subprocess_with_env(["git", "write-tree"], cwd=repo_root, env=env)
    tree_oid = (out or "").strip().splitlines()[-1] if code == 0 else None
    meta["write-tree"] = {"code": code, "tree": tree_oid}
    if code != 0 or not tree_oid:
        write_text(os.path.join(cycle_dir, "commit.meta.json"), json.dumps(meta, indent=2))
        return False, meta

    # Commit-tree
    code, out = subprocess_with_env(["git", "commit-tree", "-p", head, "-m", msg, tree_oid], cwd=repo_root, env=env)
    commit_oid = (out or "").strip().splitlines()[-1] if code == 0 else None
    meta["commit-tree"] = {"code": code, "commit": commit_oid}
    write_text(os.path.join(cycle_dir, "commit.meta.json"), json.dumps(meta, indent=2))
    if code != 0 or not commit_oid:
        return False, meta

    # Update-ref fast-forward
    ref = f"refs/heads/{branch}" if branch else "HEAD"
    code, out = subprocess_with_env(["git", "update-ref", ref, commit_oid, head], cwd=repo_root, env=env)
    meta["update-ref"] = {"code": code, "out": out, "ref": ref, "old": head, "new": commit_oid}
    write_text(os.path.join(cycle_dir, "update_ref.meta.json"), json.dumps(meta["update-ref"], indent=2))
    if code != 0:
        return False, meta

    return True, meta


def maybe_run_command(name: str, cfg: Dict[str, Any], cycle_dir: str):
    section = cfg.get("commands", {}).get(name, {})
    enabled = bool(section.get("enabled", False))
    res = {"enabled": enabled, "code": None, "output": ""}
    if not enabled:
        return res
    cmd = section.get("cmd", "")
    timeout = int(section.get("timeout_seconds", 600))
    code, out = run_cmd(cmd, timeout=timeout)
    res["code"] = code
    res["output"] = out
    # Persist full output
    write_text(os.path.join(cycle_dir, f"{name}.log"), out)

    # Screenshots artifact collection
    if name == "screenshots":
        glob_pat = section.get("collect_glob")
        if glob_pat:
            shots_dir = os.path.join(cycle_dir, "screenshots")
            cnt = collect_artifacts(glob_pat, shots_dir)
            write_text(os.path.join(cycle_dir, "screenshots", "_COLLECTION.txt"), f"collected={cnt} from {glob_pat}\n")
    return res


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    cfg_path = os.path.join(repo_root, "agent", "config.json")
    cfg = load_config(cfg_path)

    loop_cfg = cfg.get("loop", {})
    # Allow environment overrides for ad-hoc runs
    max_cycles = int(os.getenv("AGENT_MAX_CYCLES", loop_cfg.get("max_cycles", 0)))
    cooldown = int(os.getenv("AGENT_COOLDOWN_SECONDS", loop_cfg.get("cooldown_seconds", 120)))
    apply_patches = bool(loop_cfg.get("apply_patches", False))
    require_approval = bool(loop_cfg.get("require_manual_approval", True))
    patch_cfg = cfg.get("patch", {})
    path_prefix = patch_cfg.get("path_prefix")
    git_cfg = cfg.get("git", {})
    git_commit = bool(git_cfg.get("commit", False))
    git_branch = git_cfg.get("branch")
    git_push = bool(git_cfg.get("push", False))
    push_remote = git_cfg.get("remote", "origin")
    push_interval = int(git_cfg.get("push_interval_seconds", 900))

    ensure_dir(os.path.join(repo_root, "agent", "artifacts"))
    ensure_dir(os.path.join(repo_root, "agent", "inbox"))

    provider = provider_from_config(cfg)

    # Optional: switch to working branch if configured
    if git_commit and git_branch:
        run_cmd(f"git rev-parse --verify {git_branch} >/dev/null 2>&1 || git checkout -B {git_branch}")
        run_cmd(f"git checkout {git_branch}")

    cycle = 1
    while True:
        if max_cycles and cycle > max_cycles:
            break

        cycle_dir = os.path.join(repo_root, "agent", "artifacts", f"cycle_{cycle:03d}_{now_ts()}")
        ensure_dir(cycle_dir)

        # Phase 1: Analyze/Test/Screenshots
        results = {}
        results["analyze"] = maybe_run_command("analyze", cfg, cycle_dir)
        results["test"] = maybe_run_command("test", cfg, cycle_dir)
        results["e2e"] = maybe_run_command("e2e", cfg, cycle_dir)
        results["screenshots"] = maybe_run_command("screenshots", cfg, cycle_dir)

        # Phase 2: Compose prompt
        prompt = compose_prompt(repo_root, cycle_dir, results)

        # Phase 3: Provider -> get patch (or raw text)
        raw = provider.generate_patch(prompt, cycle_dir)

        patch_text = None
        if raw:
            patch_text = extract_unified_diff(raw)
            if patch_text:
                write_text(os.path.join(cycle_dir, "proposed.patch"), patch_text)
            else:
                write_text(os.path.join(cycle_dir, "provider_output_no_patch.txt"), raw)

        # Phase 4: Apply patch (optional + gated)
        if apply_patches and patch_text:
            approved = True
            if require_approval:
                approve_path = os.path.join(cycle_dir, "approve.txt")
                # Create a hint file
                if read_text(approve_path) is None:
                    write_text(approve_path, "Put 'ok' to apply this cycle's patch\n")
                approved = (read_text(approve_path) or "").strip().lower() == "ok"

            if approved:
                out = apply_patch_with_git(repo_root, patch_text, cycle_dir, path_prefix=path_prefix)
                write_text(os.path.join(cycle_dir, "apply_patch.log"), out)
                # Run analyzers and decide gate
                proposed_files = _parse_files_from_diff(patch_text)
                gate_report = _run_analyzers_and_gate(repo_root, cfg, cycle_dir, proposed_files)
                allow_commit = bool(gate_report.get("allow", True)) or bool(cfg.get("gate", {}).get("allow_override", False))
                if git_commit and allow_commit:
                    msg = _build_commit_message(repo_root, patch_text, cycle_dir)
                    ok, meta = _commit_with_temp_index(repo_root, git_branch, msg.strip(), proposed_files, cycle_dir)
                    write_text(os.path.join(cycle_dir, "cycle.meta.json"), json.dumps({
                        "commit_ok": ok,
                        "branch": git_branch,
                        "timestamp": now_ts(),
                    }, indent=2))
                    if ok and git_push and msg.startswith("agent edits:"):
                        code, pout = run_cmd(f"git push {push_remote} {git_branch}")
                        write_text(os.path.join(cycle_dir, "git_push.log"), pout)
                        write_text(os.path.join(cycle_dir, "push.meta.json"), json.dumps({"code": code, "remote": push_remote, "branch": git_branch}, indent=2))

        # Phase 5: Cooldown
        cycle += 1
        time.sleep(cooldown)


if __name__ == "__main__":
    main()
