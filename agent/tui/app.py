from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from ..providers import KeyStore

try:
    from textual import events
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import (
        Button,
        Footer,
        Header,
        Input,
        Label,
        Static,
        TabPane,
        TabbedContent,
        TextLog,
        DataTable,
        Tree,
    )
    from textual.reactive import reactive
    from textual.message import Message
except Exception as exc:  # pragma: no cover - textual optional
    raise RuntimeError("Textual is required for the agent TUI. Install with `pip install textual`." ) from exc

from rich.syntax import Syntax

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_ROOT = REPO_ROOT / "artifacts"
STATE_ROOT = REPO_ROOT / "state"
LOCAL_CONTROL = REPO_ROOT / "local" / "control"
CONFIG_PATH = REPO_ROOT / "config.json"


@dataclass
class GateSummary:
    status: str
    summary: str
    findings: List[Dict]


@dataclass
class CycleSnapshot:
    path: Optional[Path]
    meta: Dict
    gate: Optional[GateSummary]
    diff: str
    activity: str
    artifacts: List[Path]


def read_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def latest_cycle_dir() -> Optional[Path]:
    if not ARTIFACT_ROOT.exists():
        return None
    cycle_dirs = sorted(d for d in ARTIFACT_ROOT.iterdir() if d.is_dir())
    return cycle_dirs[-1] if cycle_dirs else None


def load_cycle_snapshot() -> CycleSnapshot:
    cycle_dir = latest_cycle_dir()
    meta = read_json((cycle_dir or Path()) / "cycle.meta.json") if cycle_dir else {}
    gate_data = read_json((cycle_dir or Path()) / "production_gate.json") if cycle_dir else {}
    gate_summary = None
    if gate_data:
        findings = []
        for res_name, res in gate_data.get("results", {}).items():
            for finding in res.get("findings", []):
                row = dict(finding)
                row["analyzer"] = res_name
                findings.append(row)
        gate_summary = GateSummary(
            status="allow" if gate_data.get("allow") else "blocked",
            summary=", ".join(gate_data.get("rationale", [])) or "clean",
            findings=findings,
        )
    diff_text = ""
    if cycle_dir:
        for candidate in [cycle_dir / "applied.patch", cycle_dir / "proposed.patch"]:
            if candidate.exists():
                diff_text = candidate.read_text(encoding="utf-8")
                break
    activity_parts: List[str] = []
    if cycle_dir:
        for name in ["prompt.md", "provider_output.txt", "apply_patch.log", "fast_path.log"]:
            path = cycle_dir / name
            if path.exists():
                text = path.read_text(encoding="utf-8", errors="ignore")
                activity_parts.append(f"[{name}]\n{text[:4000]}")
    activity_text = "\n\n".join(activity_parts) if activity_parts else "Waiting for activity..."
    artifacts = []
    if cycle_dir:
        for path in cycle_dir.rglob("*"):
            if path.is_file():
                artifacts.append(path)
    return CycleSnapshot(
        path=cycle_dir,
        meta=meta,
        gate=gate_summary,
        diff=diff_text,
        activity=activity_text,
        artifacts=artifacts,
    )


def write_control(name: str, content: str = "") -> None:
    LOCAL_CONTROL.mkdir(parents=True, exist_ok=True)
    target = LOCAL_CONTROL / f"{name}.cmd"
    target.write_text(content.strip(), encoding="utf-8")


class ActivityPanel(TextLog):
    def update_activity(self, text: str) -> None:
        self.clear()
        for line in text.splitlines():
            self.write(line)


class DiffPanel(Static):
    def update_diff(self, diff_text: str) -> None:
        if not diff_text:
            self.update("No diff available yet.")
            return
        syntax = Syntax(diff_text, "diff", theme="ansi_dark", line_numbers=False)
        self.update(syntax)


class FindingsPanel(DataTable):
    columns_defined = False

    def update_findings(self, gate: Optional[GateSummary]) -> None:
        if not self.columns_defined:
            self.clear(columns=True)
            self.add_columns("Analyzer", "Severity", "Message", "Path", "Line")
            self.columns_defined = True
        self.clear(rows=True)
        if not gate or not gate.findings:
            self.add_row("-", "-", "No findings", "", "")
            return
        for item in gate.findings:
            self.add_row(
                item.get("analyzer", ""),
                item.get("severity", ""),
                item.get("message", ""),
                item.get("path", ""),
                str(item.get("line", "")),
            )


class ArtifactTree(Tree):
    def update_artifacts(self, artifacts: List[Path], base: Optional[Path]) -> None:
        if not base:
            self.root.label = "No cycles yet"
            self.root.children.clear()
            return
        self.root.label = base.name
        self.root.children.clear()
        for path in artifacts:
            try:
                rel = path.relative_to(base)
            except ValueError:
                rel = path
            self.root.add(str(rel))
        self.root.expand_all()


class ConfigPanel(Static):
    def update_config(self) -> None:
        if CONFIG_PATH.exists():
            self.update(CONFIG_PATH.read_text(encoding="utf-8"))
        else:
            self.update("config.json missing")


class CommitStatus(Static):
    auto_commit = reactive(True)
    cadence = reactive(3600)

    def update_commit_state(self) -> None:
        meta = read_json(STATE_ROOT / "commit_scheduler.json")
        self.auto_commit = bool(meta.get("auto_commit", True))
        self.cadence = int(meta.get("cadence_seconds", 3600))
        next_at = meta.get("next_commit_at")
        summary = f"Auto-commit: {'ON' if self.auto_commit else 'OFF'} | Cadence: {self.cadence}s"
        if next_at:
            summary += f" | Next: {next_at:.0f}"
        self.update(summary)


class SessionStatus(Static):
    def update_session(self) -> None:
        meta = read_json(STATE_ROOT / "session.json")
        if not meta:
            self.update("Session: inactive")
            return
        scope = meta.get("active_scope")
        status = meta.get("status", "idle")
        self.update(f"Session: {status} ({scope or 'none'})")


class Sidebar(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Tasks", id="sidebar-title")
        yield Button("Analyze", id="btn-analyze")
        yield Button("Fix Style", id="btn-style")
        yield Button("Fix Security", id="btn-security")
        yield Button("Run Tests", id="btn-tests")
        yield Button("Enhance Codebase", id="btn-enhance")
        yield Button("UI Audits", id="btn-ui")
        yield Static("\nCommit & Sessions", classes="section-title")
        self.commit_status = CommitStatus(id="commit-status")
        yield self.commit_status
        self.session_status = SessionStatus(id="session-status")
        yield self.session_status
        yield Button("Commit Now", id="btn-commit-now")
        yield Button("Toggle Auto-Commit", id="btn-toggle-commit")
        yield Button("Start Session", id="btn-session-start")
        yield Button("Stop Session", id="btn-session-stop")
        yield Static("\nSlash commands available via input below.", classes="help")

    def update_state(self) -> None:
        self.commit_status.update_commit_state()
        self.session_status.update_session()


class ModelsPanel(Static):
    def update_models(self) -> None:
        cfg = read_json(CONFIG_PATH)
        provider = cfg.get("provider", {})
        lines = ["Provider configuration:"]
        if provider:
            lines.append(json.dumps(provider, indent=2))
        else:
            lines.append("No provider configured")
        self.update("\n".join(lines))


class ApiKeyPanel(Static):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.keystore = KeyStore()

    def update_keys(self) -> None:
        cfg = read_json(CONFIG_PATH)
        provider = cfg.get("provider", {})
        keys = []
        if provider.get("type") == "api":
            api_cfg = provider.get("api", {})
            key_id = api_cfg.get("key_id", api_cfg.get("backend", "api"))
            secret = self.keystore.get(key_id)
            keys.append((key_id, secret is not None))
        else:
            for name in ("openai", "anthropic", "azure"):
                secret = self.keystore.get(name)
                if secret:
                    keys.append((name, True))
        if not keys:
            self.update("No API keys stored.")
            return
        display = [f"{name}: {'set' if present else 'missing'}" for name, present in keys]
        self.update("\n".join(display))

class AgentApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #view {
    }
    #main-container {
        height: 1fr;
    }
    Vertical.sidebar {
        width: 32;
        background: $panel-darken-2;
        padding: 1 1;
        border: tall $secondary;
    }
    Vertical.sidebar Button {
        margin: 0 0 1 0;
    }
    #activity-log {
        border: tall $accent;
    }
    #command-input {
        dock: bottom;
    }
    TabbedContent {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("c", "commit_now", "Commit Now"),
        Binding("a", "toggle_auto_commit", "Auto-Commit"),
        Binding("s", "toggle_session", "Start/Stop Session"),
        Binding("d", "open_diff", "Diff"),
        Binding("f", "open_findings", "Findings"),
        Binding("g", "open_findings", "Gate"),
        Binding("m", "open_models", "Models"),
        Binding("k", "open_keys", "API Keys"),
        Binding("u", "open_ui", "UI Audits"),
        Binding("?", "show_help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        container = Horizontal(id="main-container")
        container.mount(Sidebar(classes="sidebar"))
        center = Vertical()
        self.activity = ActivityPanel(id="activity-log")
        center.mount(Label("Thinking & Actions", id="center-title"))
        center.mount(self.activity)
        container.mount(center)
        right = Vertical(id="right-pane")
        self.diff_panel = DiffPanel()
        self.findings_panel = FindingsPanel()
        self.artifacts_panel = ArtifactTree("Artifacts")
        self.config_panel = ConfigPanel()
        self.models_panel = ModelsPanel()
        self.keys_panel = ApiKeyPanel()
        right.mount(
            TabbedContent(
                TabPane("Diff", self.diff_panel, id="tab-diff"),
                TabPane("Findings", self.findings_panel, id="tab-findings"),
                TabPane("Artifacts", self.artifacts_panel, id="tab-artifacts"),
                TabPane("Config", self.config_panel, id="tab-config"),
                TabPane("Models", self.models_panel, id="tab-models"),
                TabPane("API Keys", self.keys_panel, id="tab-keys"),
            )
        )
        container.mount(right)
        yield container
        self.command_input = Input(placeholder="Type /command and press Enter", id="command-input")
        yield self.command_input
        yield Footer()

    def on_mount(self) -> None:
        self.sidebar = self.query_one(Sidebar)
        self.set_interval(2.5, self.refresh_state)
        self.refresh_state()

    def refresh_state(self) -> None:
        snapshot = load_cycle_snapshot()
        self.sidebar.update_state()
        self.activity.update_activity(snapshot.activity)
        self.diff_panel.update_diff(snapshot.diff)
        self.findings_panel.update_findings(snapshot.gate)
        self.artifacts_panel.update_artifacts(snapshot.artifacts, snapshot.path)
        self.config_panel.update_config()
        self.models_panel.update_models()
        self.keys_panel.update_keys()

    def action_commit_now(self) -> None:
        write_control("commit_now", "now")
        self.bell()

    def action_toggle_auto_commit(self) -> None:
        meta = read_json(STATE_ROOT / "commit_scheduler.json")
        enabled = not bool(meta.get("auto_commit", True))
        write_control("auto_commit", "on" if enabled else "off")
        self.refresh_state()

    def action_toggle_session(self) -> None:
        meta = read_json(STATE_ROOT / "session.json")
        status = meta.get("status") if meta else "idle"
        if status == "running":
            write_control("session", "stop")
        else:
            write_control("session", "start scope=repo")
        self.refresh_state()

    def action_open_diff(self) -> None:
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab-diff"

    def action_open_findings(self) -> None:
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab-findings"

    def action_open_models(self) -> None:
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab-models"

    def action_open_keys(self) -> None:
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab-keys"

    def action_open_ui(self) -> None:
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab-findings"

    def action_show_help(self) -> None:
        self.activity.update_activity(
            "Commands:\n/commit now | /commit on|off | /cadence 900 | /session start scope=path dur=3600 review=1800 | /session stop"
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        mapping = {
            "btn-commit-now": self.action_commit_now,
            "btn-toggle-commit": self.action_toggle_auto_commit,
            "btn-session-start": lambda: write_control("session", "start scope=repo"),
            "btn-session-stop": lambda: write_control("session", "stop"),
        }
        handler = mapping.get(event.button.id)
        if handler:
            handler()
            self.refresh_state()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = (event.value or "").strip()
        self.command_input.value = ""
        if not text.startswith("/"):
            return
        self.handle_command(text[1:])
        self.refresh_state()

    def handle_command(self, command: str) -> None:
        parts = command.split()
        if not parts:
            return
        name = parts[0]
        if name == "commit" and len(parts) > 1:
            if parts[1] == "now":
                self.action_commit_now()
            elif parts[1] in {"on", "off"}:
                write_control("auto_commit", parts[1])
        elif name == "cadence" and len(parts) > 1:
            write_control("cadence", parts[1])
        elif name == "session":
            payload = " ".join(parts[1:]) or "start scope=repo"
            write_control("session", payload)
        elif name == "model" and len(parts) > 1:
            write_control("model", parts[1])
        elif name == "apikey" and len(parts) > 1:
            write_control("apikey", " ".join(parts[1:]))
        self.refresh_state()


def launch_app() -> int:
    app = AgentApp()
    app.run()
    return 0
