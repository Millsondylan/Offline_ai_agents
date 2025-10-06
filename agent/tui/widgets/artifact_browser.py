from __future__ import annotations

from typing import List

from textual.containers import Vertical, VerticalScroll
from textual.widgets import Label, Static

from ..navigation import NavEntry, NavigationItem
from ..state_watcher import ArtifactState


class ArtifactButton(NavigationItem):
    def __init__(self, artifact: ArtifactState, label: str, index: int) -> None:
        self.artifact = artifact
        super().__init__(label, "Open artifact", id=f"artifact-{index}")

    def handle_enter(self) -> None:  # type: ignore[override]
        getattr(self.app, "open_artifact", lambda _artifact: None)(self.artifact)


class ArtifactBrowser(Static):
    def __init__(self) -> None:
        super().__init__(id="artifact-browser")
        self.title = Label("═══ ARTIFACTS ═══", classes="panel-title")
        self.artifact_scroll = VerticalScroll(id="artifact-scroll")
        self.container = Vertical(id="artifact-container")
        self._nav_entries: List[NavEntry] = []
        self._empty_label: Label | None = None

    def compose(self):
        self.artifact_scroll.can_focus = False

        with Vertical(id="artifact-panel"):
            yield self.title
            with self.artifact_scroll:
                yield self.container

    def update_artifacts(self, artifacts: List[ArtifactState]) -> None:
        # Check if we need to update
        existing_count = sum(1 for child in self.container.children if hasattr(child, 'id') and child.id and child.id.startswith('artifact-'))
        new_count = len(artifacts)

        if existing_count == new_count and existing_count > 0:
            return

        # Clear existing
        for child in list(self.container.children):
            try:
                child.remove()
            except Exception:
                pass

        self._nav_entries = []
        if not artifacts:
            if self._empty_label is None:
                self._empty_label = Label("No artifacts yet", classes="dim")
            if self._empty_label not in self.container.children:
                self.container.mount(self._empty_label)
            self.refresh()
            return

        current_folder: str | None = None
        counter = 0
        for artifact in artifacts:
            parts = artifact.label.split("/")
            folder = parts[0] if parts else "artifacts"
            if folder != current_folder:
                current_folder = folder
                self.container.mount(Label(f"📁 {folder}/", classes="artifact-folder"))
            depth = max(0, len(parts) - 2)
            indent = "  " * depth
            name = parts[-1] if parts else artifact.path.name
            label = f"{indent}📄 {name} - Open file in viewer (press ENTER)"
            button = ArtifactButton(artifact, label, counter)
            self.container.mount(button)
            widget_id = button.id or f"artifact-{counter}"
            self._nav_entries.append(NavEntry(widget_id=widget_id, action=f"View artifact: {name}"))
            counter += 1
        self.refresh()

    def nav_entries(self) -> List[NavEntry]:
        return list(self._nav_entries)
