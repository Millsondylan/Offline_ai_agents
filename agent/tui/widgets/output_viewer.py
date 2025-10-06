from __future__ import annotations

import json
from typing import List, Optional

from rich.syntax import Syntax

from textual import events
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Log

from ..navigation import NavEntry, NavigationItem
from ..state_watcher import ArtifactState


class TabButton(NavigationItem):
    def __init__(self, name: str, viewer: "OutputViewer", index: int) -> None:
        self.tab_name = name
        self.viewer = viewer
        super().__init__(name.title(), f"Show {name} tab", id=f"tab-{name}")

    def handle_enter(self) -> None:  # type: ignore[override]
        if self.tab_name == "config":
            if self.viewer.active_tab != "config":
                self.viewer.select_tab("config")
            else:
                self.viewer.toggle_config_editor()
        else:
            self.viewer.select_tab(self.tab_name)


class DiffActionButton(NavigationItem):
    def __init__(self, label: str, action: str, callback_name: str, button_id: str) -> None:
        super().__init__(label, action, id=button_id)
        self.callback_name = callback_name

    def handle_enter(self) -> None:  # type: ignore[override]
        getattr(self.app, self.callback_name, lambda: None)()


class ConfigLineButton(NavigationItem):
    def __init__(self, viewer: "OutputViewer", key: str, value: object, index: int) -> None:
        self.viewer = viewer
        self.key = key
        self.value = value
        self.editing = False
        self.buffer = ""
        label = self._format_label(value)
        super().__init__(label, f"Edit {key}", id=f"config-line-{index}")

    def _format_label(self, value: object) -> str:
        rendered = self.viewer.format_config_value(value)
        return f"{self.key}: {rendered}"

    def set_value(self, value: object) -> None:
        self.value = value
        self.set_display(self._format_label(value))
        self.enter_action = f"Edit {self.key}"

    def start_edit(self) -> None:
        self.editing = True
        self.buffer = self.viewer.format_config_value(self.value)
        self.set_display(f"{self.key}: {self.buffer}|")
        self.enter_action = f"Save {self.key}"

    def finish_edit(self) -> None:
        self.editing = False
        self.buffer = ""
        self.set_display(self._format_label(self.value))
        self.enter_action = f"Edit {self.key}"

    def handle_enter(self) -> None:  # type: ignore[override]
        if self.editing:
            self.viewer.commit_config_line(self, self.buffer)
        else:
            self.start_edit()

    def on_blur(self, event: events.Blur) -> None:  # type: ignore[override]
        super().on_blur(event)
        if self.editing:
            self.finish_edit()

    def on_key(self, event: events.Key) -> None:  # type: ignore[override]
        if not self.editing:
            return
        if event.key == "backspace":
            self.buffer = self.buffer[:-1]
        elif event.character and event.character.isprintable():
            self.buffer += event.character
        elif len(event.key) == 1 and event.key.isprintable():
            self.buffer += event.key
        else:
            return
        event.stop()
        self.set_display(f"{self.key}: {self.buffer}|")


class OutputViewer(Static):
    def __init__(self) -> None:
        super().__init__(id="output-viewer")
        self.tabs_row = Horizontal(id="output-tabs")
        self.diff_panel = Static(id="diff-panel")
        self.findings_panel = Log(id="findings-panel")
        self.logs_panel = Log(id="logs-panel")
        self.config_panel = Static(id="config-panel")
        self.config_lines_container = Vertical(id="config-lines")
        self.config_lines_container.display = False
        self.tab_buttons = {
            "diff": TabButton("diff", self, 0),
            "findings": TabButton("findings", self, 1),
            "logs": TabButton("logs", self, 2),
            "config": TabButton("config", self, 3),
        }
        self.apply_button = DiffActionButton("[Apply All]", "Apply all diffs", "apply_all_diffs", "diff-apply")
        self.reject_button = DiffActionButton("[Reject All]", "Reject all diffs", "reject_all_diffs", "diff-reject")
        self._active_tab = "diff"
        self._findings: List[dict] = []
        self._gate_filter: Optional[str] = None
        self.config_line_buttons: List[ConfigLineButton] = []
        self._config_json: dict = {}
        self._config_expanded = False

    @property
    def active_tab(self) -> str:
        return self._active_tab

    def compose(self):
        for button in self.tab_buttons.values():
            self.tabs_row.mount(button)
        self.findings_panel.styles.auto_scroll = True
        self.logs_panel.styles.auto_scroll = True
        yield self.tabs_row
        yield self.diff_panel
        yield self.findings_panel
        yield self.logs_panel
        yield self.config_panel
        yield self.config_lines_container
        yield Horizontal(self.apply_button, self.reject_button, id="diff-actions")
        self.select_tab(self._active_tab)

    # ------------------------------------------------------------------
    # Navigation exposure
    # ------------------------------------------------------------------

    def nav_entries(self) -> List[NavEntry]:
        entries = [
            NavEntry(widget_id=btn.id or f"tab-{name}", action=btn.enter_action)
            for name, btn in self.tab_buttons.items()
        ]
        if self._config_expanded:
            entries.extend(
                NavEntry(widget_id=btn.id or f"config-line-{idx}", action=btn.enter_action)
                for idx, btn in enumerate(self.config_line_buttons)
                if btn.id
            )
        entries.append(NavEntry(widget_id=self.apply_button.id or "diff-apply", action=self.apply_button.enter_action))
        entries.append(NavEntry(widget_id=self.reject_button.id or "diff-reject", action=self.reject_button.enter_action))
        return entries

    # ------------------------------------------------------------------
    # Tab selection & rendering
    # ------------------------------------------------------------------

    def select_tab(self, name: str) -> None:
        if name != "config" and self._config_expanded:
            self._collapse_config_editor()
        self._active_tab = name
        self.diff_panel.display = name == "diff"
        self.findings_panel.display = name == "findings"
        self.logs_panel.display = name == "logs"
        self.config_panel.display = name == "config" and not self._config_expanded
        self.config_lines_container.display = name == "config" and self._config_expanded
        if name == "findings":
            self._render_findings()
        elif name == "config" and self._config_expanded:
            self._render_config_lines()

    def toggle_config_editor(self) -> None:
        if not self._config_expanded:
            self._expand_config_editor()
        else:
            self._collapse_config_editor()

    def _expand_config_editor(self) -> None:
        self._config_expanded = True
        self._render_config_lines()
        self.config_panel.display = False
        self.config_lines_container.display = True
        getattr(self.app, "rebuild_navigation", lambda: None)()

    def _collapse_config_editor(self) -> None:
        for button in self.config_line_buttons:
            button.finish_edit()
        for child in list(self.config_lines_container.children):
            child.remove()
        self.config_line_buttons = []
        self._config_expanded = False
        self.config_lines_container.display = False
        self.config_panel.display = True
        getattr(self.app, "rebuild_navigation", lambda: None)()

    def _render_config_lines(self) -> None:
        for child in list(self.config_lines_container.children):
            child.remove()
        self.config_line_buttons = []
        editable_items = [item for item in self._config_json.items() if not isinstance(item[1], (dict, list))]
        if not editable_items:
            self.config_lines_container.mount(Static("No editable config entries", classes="dim"))
            return
        for index, (key, value) in enumerate(sorted(editable_items, key=lambda item: item[0])):
            button = ConfigLineButton(self, key, value, index)
            self.config_lines_container.mount(button)
            self.config_line_buttons.append(button)

    # ------------------------------------------------------------------
    # Data updaters
    # ------------------------------------------------------------------

    def update_diff(self, diff_text: str) -> None:
        if diff_text:
            syntax = Syntax(diff_text, "diff", theme="ansi_dark", line_numbers=False)
            self.diff_panel.update(syntax)
        else:
            self.diff_panel.update("No diff available.")

    def update_findings(self, findings: List[dict]) -> None:
        self._findings = findings or []
        if self._active_tab == "findings":
            self._render_findings()

    def update_logs(self, lines: List[str]) -> None:
        self.logs_panel.clear()
        if not lines:
            self.logs_panel.write("No logs yet.")
            return
        for line in lines:
            self.logs_panel.write(line)

    def update_config(self, config_text: str) -> None:
        self._config_json = {}
        pretty = config_text
        try:
            parsed = json.loads(config_text)
            if isinstance(parsed, dict):
                self._config_json = parsed
                pretty = json.dumps(parsed, indent=2, sort_keys=True)
            else:
                pretty = json.dumps(parsed, indent=2, sort_keys=True)
        except Exception:
            pass
        self.config_panel.update(Syntax(pretty, "json", theme="ansi_dark", line_numbers=True))
        if self._active_tab == "config" and self._config_expanded:
            self._render_config_lines()
            getattr(self.app, "rebuild_navigation", lambda: None)()

    def filter_findings(self, gate_name: Optional[str]) -> None:
        self._gate_filter = gate_name
        if self._active_tab == "findings":
            self._render_findings()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _render_findings(self) -> None:
        self.findings_panel.clear()
        if not self._findings:
            self.findings_panel.write("No findings.")
            return
        displayed = False
        for item in self._findings:
            gate = item.get("analyzer") or item.get("gate") or "unknown"
            if self._gate_filter and gate != self._gate_filter:
                continue
            severity = item.get("severity", "info")
            path = item.get("path") or item.get("file") or "--"
            line = item.get("line") or item.get("lineno") or "--"
            message = item.get("message") or item.get("summary") or ""
            self.findings_panel.write(f"[{severity.upper()}] {gate} :: {path}:{line} :: {message}")
            displayed = True
        if self._gate_filter and not displayed:
            self.findings_panel.write(f"No findings for gate {self._gate_filter}.")

    def format_config_value(self, value: object) -> str:
        try:
            return json.dumps(value)
        except TypeError:
            return str(value)

    def commit_config_line(self, button: ConfigLineButton, raw_value: str) -> None:
        text = raw_value.strip()
        if not text:
            button.finish_edit()
            return
        try:
            new_value = json.loads(text)
        except json.JSONDecodeError:
            new_value = text
        self._config_json[button.key] = new_value
        button.set_value(new_value)
        button.finish_edit()
        pretty = json.dumps(self._config_json, indent=2, sort_keys=True)
        self.config_panel.update(Syntax(pretty, "json", theme="ansi_dark", line_numbers=True))
        getattr(self.app, "save_config", lambda _cfg: None)(self._config_json)

    def load_artifact(self, artifact: ArtifactState) -> None:
        kind = artifact.kind
        try:
            text = artifact.path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
        if kind == "diff":
            self.update_diff(text)
            self.select_tab("diff")
        elif kind == "findings":
            try:
                data = json.loads(text)
            except Exception:
                data = []
            findings = data if isinstance(data, list) else data.get("findings", []) if isinstance(data, dict) else []
            self.update_findings(findings)
            self.select_tab("findings")
        elif kind == "log":
            lines = text.splitlines()
            self.update_logs(lines)
            self.select_tab("logs")
        else:
            self.config_panel.update(Syntax(text, "text", theme="ansi_dark"))
            self.select_tab("config")
