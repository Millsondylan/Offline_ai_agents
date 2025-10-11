from __future__ import annotations

from pathlib import Path

import pytest
from agent_cli.panels.code_editor import (
    CTRL_S,
    KEY_DOWN,
    KEY_ESC,
    KEY_UP,
    CodeEditorPanel,
)


@pytest.fixture()
def editor_root(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    (project / "main.py").write_text("print('hello')\n")
    (project / "README.md").write_text("# Title\n")
    readonly = project / "locked.txt"
    readonly.write_text("secure\n")
    readonly.chmod(0o444)
    return project


def _panel(editor_root: Path, stub_interaction) -> CodeEditorPanel:
    return CodeEditorPanel(root_path=editor_root, interaction=stub_interaction)


def test_lists_files_with_metadata(editor_root, stub_interaction):
    panel = _panel(editor_root, stub_interaction)
    names = [info.path.name for info in panel.files]
    assert {"main.py", "README.md", "locked.txt"}.issubset(set(names))
    locked = next(info for info in panel.files if info.path.name == "locked.txt")
    assert locked.is_readonly is True


def test_open_file_displays_content(fake_screen, theme_manager, editor_root, stub_interaction):
    panel = _panel(editor_root, stub_interaction)
    target = next(info for info in panel.files if info.path.name == "main.py")
    panel.open_file(target.path)
    panel.render(fake_screen, theme_manager)
    assert fake_screen.contains("print('hello')")


def test_edit_mode_allows_typing(editor_root, stub_interaction):
    panel = _panel(editor_root, stub_interaction)
    target = next(info for info in panel.files if info.path.name == "main.py")
    panel.open_file(target.path)
    panel.handle_key(ord("E"))
    panel.handle_key(ord("!"))
    assert panel.content_lines[0].startswith("!print")
    assert panel.is_modified is True


def test_ctrl_s_saves_changes(editor_root, stub_interaction):
    panel = _panel(editor_root, stub_interaction)
    target = next(info for info in panel.files if info.path.name == "main.py")
    panel.open_file(target.path)
    panel.handle_key(ord("E"))
    panel.handle_key(ord("!"))
    panel.handle_key(CTRL_S)
    assert "!" in (panel.current_file.read_text())
    assert panel.is_modified is False


def test_escape_prompts_when_modified(editor_root, stub_interaction):
    panel = _panel(editor_root, stub_interaction)
    target = next(info for info in panel.files if info.path.name == "main.py")
    panel.open_file(target.path)
    panel.handle_key(ord("E"))
    panel.handle_key(ord("!"))
    stub_interaction.queue_confirm(True)
    panel.handle_key(KEY_ESC)
    assert panel.is_editing is False
    assert panel.is_modified is False


def test_large_file_scroll(editor_root, stub_interaction):
    large_file = editor_root / "big.txt"
    large_file.write_text("\n".join(f"Line {i}" for i in range(2000)))
    panel = _panel(editor_root, stub_interaction)
    panel.open_file(large_file)
    panel.handle_key(KEY_DOWN)
    assert panel.scroll_offset > 0
    panel.handle_key(KEY_UP)
    assert panel.scroll_offset == 0
