"""Generate deterministic navigation data for the compatibility TUI."""

from __future__ import annotations

import json
from pathlib import Path

DATA_PATH = Path(__file__).with_name("generated_navigation.json")


def generate() -> Path:
    """Create a large synthetic navigation data set."""
    entries = []

    for idx in range(60):
        entries.append({"widget_id": f"task_{idx:03d}", "label": f"Task {idx:03d}"})

    for idx in range(20):
        entries.append({"widget_id": f"gate_{idx:02d}", "label": f"Gate {idx:02d}"})

    for idx in range(40):
        entries.append({"widget_id": f"artifact_{idx:03d}", "label": f"Artifact {idx:03d}"})

    control_buttons = [
        {"widget_id": "control_pause", "label": "Pause"},
        {"widget_id": "control_resume", "label": "Resume"},
        {"widget_id": "control_stop", "label": "Stop"},
        {"widget_id": "control_commit", "label": "Force Commit"},
    ]
    entries.extend(control_buttons)

    tabs = [
        {"widget_id": "tab_diff", "label": "Diff"},
        {"widget_id": "tab_logs", "label": "Logs"},
        {"widget_id": "tab_findings", "label": "Findings"},
        {"widget_id": "tab_config", "label": "Config"},
    ]
    entries.extend(tabs)

    diff_actions = [
        {"widget_id": "diff_apply", "label": "Apply Diff"},
        {"widget_id": "diff_reject", "label": "Reject Diff"},
    ]
    entries.extend(diff_actions)

    DATA_PATH.write_text(json.dumps(entries, indent=2))
    return DATA_PATH


def main() -> None:
    path = generate()
    print(f"Generated navigation data at {path}")


if __name__ == "__main__":
    main()
