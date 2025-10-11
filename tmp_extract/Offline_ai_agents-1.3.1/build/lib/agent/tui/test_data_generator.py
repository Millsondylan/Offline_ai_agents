#!/usr/bin/env python3
"""Generate test data for TUI testing."""
import json
from pathlib import Path


def generate_test_data():
    """Generate test state files with 50+ items."""
    state_dir = Path(__file__).parent.parent / "state"
    artifacts_dir = Path(__file__).parent.parent / "artifacts"

    state_dir.mkdir(exist_ok=True)
    artifacts_dir.mkdir(exist_ok=True)

    # Generate session.json with running state
    session = {
        "status": "running",
        "cycle_count": 42,
        "current_cycle": 42,
        "phase": "executing",
        "elapsed_seconds": 125,
        "estimated_seconds": 300,
        "session_duration": 7200,
        "fastpath_files": ["src/main.py", "src/utils.py", "tests/test_main.py"]
    }
    (state_dir / "session.json").write_text(json.dumps(session, indent=2))

    # Generate scheduler.json with 60 tasks
    tasks = []
    statuses = ["running", "pending", "paused", "complete"]
    for i in range(60):
        status = statuses[i % len(statuses)]
        tasks.append({
            "id": f"task_{i:03d}",
            "name": f"Task {i}: Implement feature {chr(65 + i % 26)}",
            "status": status
        })

    scheduler = {"tasks": tasks}
    (state_dir / "scheduler.json").write_text(json.dumps(scheduler, indent=2))

    # Generate cycle metadata with 20 gates
    cycle_dir = artifacts_dir / "cycle_042"
    cycle_dir.mkdir(exist_ok=True)

    gates = {}
    gate_names = [
        "ruff", "bandit", "mypy", "pytest", "black", "isort",
        "pylint", "flake8", "coverage", "security-check",
        "type-check", "lint-imports", "check-docs", "validate-api",
        "test-integration", "performance", "memory-leak", "thread-safety",
        "sql-injection", "xss-check"
    ]

    for i, name in enumerate(gate_names):
        passed = i % 3 != 0  # 2/3 pass, 1/3 fail
        findings = [] if passed else [
            {"severity": "error", "message": f"Issue in {name}", "path": f"src/file_{i}.py", "line": i * 10}
            for _ in range(3)
        ]
        gates[name] = {
            "passed": passed,
            "findings": findings
        }

    cycle_meta = {"gates": gates}
    (cycle_dir / "cycle.meta.json").write_text(json.dumps(cycle_meta, indent=2))

    # Generate findings
    all_findings = []
    for gate_name, gate_data in gates.items():
        all_findings.extend([
            {
                "analyzer": gate_name,
                "severity": "error" if not gate_data["passed"] else "info",
                "path": f.get("path", "unknown"),
                "line": f.get("line", 0),
                "message": f.get("message", "")
            }
            for f in gate_data["findings"]
        ])

    (cycle_dir / "findings.json").write_text(json.dumps(all_findings, indent=2))

    # Generate diff.patch
    diff_content = """--- a/src/main.py
+++ b/src/main.py
@@ -10,7 +10,7 @@ def main():
     parser = argparse.ArgumentParser()
     parser.add_argument('--config', type=str)
-    args = parser.parse_args()
+    args = parser.parse_args(sys.argv[1:])

     if args.config:
         load_config(args.config)
@@ -25,3 +25,8 @@ def load_config(path):
     with open(path) as f:
         config = json.load(f)
     return config
+
+def new_feature():
+    '''New feature implementation.'''
+    print('Feature enabled')
+    return True
"""
    (cycle_dir / "diff.patch").write_text(diff_content)

    # Generate agent.log
    log_lines = [
        f"[{i:04d}] INFO: Processing task {i}" for i in range(200)
    ]
    (cycle_dir / "agent.log").write_text("\n".join(log_lines))

    # Generate 40 artifact files across multiple cycles
    for cycle_num in range(35, 43):
        cycle_path = artifacts_dir / f"cycle_{cycle_num:03d}"
        cycle_path.mkdir(exist_ok=True)

        (cycle_path / f"diff_{cycle_num}.patch").write_text(f"diff for cycle {cycle_num}")
        (cycle_path / f"findings_{cycle_num}.json").write_text("[]")
        (cycle_path / f"log_{cycle_num}.txt").write_text(f"log {cycle_num}")

    print("✓ Generated test data:")
    print("  - 60 tasks")
    print("  - 20 gates")
    print("  - 40+ artifacts")
    print(f"  - State files in {state_dir}")
    print(f"  - Artifacts in {artifacts_dir}")


if __name__ == "__main__":
    generate_test_data()
