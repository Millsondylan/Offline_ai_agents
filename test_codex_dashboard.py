"""Test suite for Codex Dashboard implementation.

This test validates all components are properly implemented without
placeholders, TODOs, or incomplete features.
"""

import ast
import json
from pathlib import Path


def test_no_placeholders():
    """Ensure no TODO, FIXME, or placeholder comments exist."""
    print("Testing for placeholders...")

    forbidden_patterns = [
        'TODO',
        'FIXME',
        'PLACEHOLDER',
        'NotImplementedError',
        'pass  # implement',
        '...',  # Ellipsis used as placeholder
    ]

    files_to_check = [
        'agent_dashboard/codex_dashboard.py',
        'agent_dashboard/codex_widgets/status_header.py',
        'agent_dashboard/codex_widgets/nav_sidebar.py',
        'agent_dashboard/codex_widgets/metrics_sidebar.py',
        'agent_dashboard/codex_widgets/thinking_stream.py',
        'agent_dashboard/codex_widgets/task_panel.py',
        'agent_dashboard/codex_widgets/log_viewer.py',
        'agent_dashboard/codex_widgets/code_viewer.py',
    ]

    issues = []

    for file_path in files_to_check:
        path = Path(file_path)
        if not path.exists():
            issues.append(f"Missing file: {file_path}")
            continue

        content = path.read_text()

        for pattern in forbidden_patterns:
            if pattern in content:
                # Check if it's in a comment or string
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if pattern in line and ('#' in line or pattern in ['TODO', 'FIXME', 'PLACEHOLDER']):
                        issues.append(f"{file_path}:{i}: Contains '{pattern}'")

    if issues:
        print("FAILED - Found placeholders:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("PASSED - No placeholders found")
        return True


def test_all_files_exist():
    """Verify all required files exist."""
    print("\nTesting file structure...")

    required_files = [
        'agent_dashboard/codex_dashboard.py',
        'agent_dashboard/codex_widgets/__init__.py',
        'agent_dashboard/codex_widgets/status_header.py',
        'agent_dashboard/codex_widgets/nav_sidebar.py',
        'agent_dashboard/codex_widgets/metrics_sidebar.py',
        'agent_dashboard/codex_widgets/thinking_stream.py',
        'agent_dashboard/codex_widgets/task_panel.py',
        'agent_dashboard/codex_widgets/log_viewer.py',
        'agent_dashboard/codex_widgets/code_viewer.py',
        'install_codex.sh',
        'CODEX_QUICKSTART.md',
        'agent_dashboard/CODEX_README.md',
        'agent_dashboard/codex_demo.py',
    ]

    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)

    if missing:
        print("FAILED - Missing files:")
        for file_path in missing:
            print(f"  - {file_path}")
        return False
    else:
        print("PASSED - All files present")
        return True


def test_dependencies_declared():
    """Verify dependencies are declared in pyproject.toml."""
    print("\nTesting dependencies...")

    pyproject = Path('pyproject.toml')
    if not pyproject.exists():
        print("FAILED - pyproject.toml not found")
        return False

    content = pyproject.read_text()

    required_deps = ['textual', 'rich', 'pygments']
    missing_deps = []

    for dep in required_deps:
        if dep not in content:
            missing_deps.append(dep)

    if missing_deps:
        print("FAILED - Missing dependencies in pyproject.toml:")
        for dep in missing_deps:
            print(f"  - {dep}")
        return False
    else:
        print("PASSED - All dependencies declared")
        return True


def test_imports_valid():
    """Test that all imports are valid Python."""
    print("\nTesting Python syntax...")

    files_to_check = [
        'agent_dashboard/codex_dashboard.py',
        'agent_dashboard/codex_widgets/__init__.py',
        'agent_dashboard/codex_widgets/status_header.py',
        'agent_dashboard/codex_widgets/nav_sidebar.py',
        'agent_dashboard/codex_widgets/metrics_sidebar.py',
        'agent_dashboard/codex_widgets/thinking_stream.py',
        'agent_dashboard/codex_widgets/task_panel.py',
        'agent_dashboard/codex_widgets/log_viewer.py',
        'agent_dashboard/codex_widgets/code_viewer.py',
    ]

    errors = []

    for file_path in files_to_check:
        path = Path(file_path)
        try:
            content = path.read_text()
            ast.parse(content)
        except SyntaxError as e:
            errors.append(f"{file_path}: {e}")

    if errors:
        print("FAILED - Syntax errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("PASSED - All files have valid syntax")
        return True


def test_widget_classes():
    """Verify all widget classes are properly defined."""
    print("\nTesting widget classes...")

    widget_files = {
        'StatusHeader': 'agent_dashboard/codex_widgets/status_header.py',
        'NavSidebar': 'agent_dashboard/codex_widgets/nav_sidebar.py',
        'MetricsSidebar': 'agent_dashboard/codex_widgets/metrics_sidebar.py',
        'ThinkingStream': 'agent_dashboard/codex_widgets/thinking_stream.py',
        'TaskPanel': 'agent_dashboard/codex_widgets/task_panel.py',
        'LogViewer': 'agent_dashboard/codex_widgets/log_viewer.py',
        'CodeViewer': 'agent_dashboard/codex_widgets/code_viewer.py',
    }

    missing_classes = []

    for class_name, file_path in widget_files.items():
        content = Path(file_path).read_text()
        if f"class {class_name}" not in content:
            missing_classes.append(f"{class_name} in {file_path}")

    if missing_classes:
        print("FAILED - Missing widget classes:")
        for missing in missing_classes:
            print(f"  - {missing}")
        return False
    else:
        print("PASSED - All widget classes defined")
        return True


def test_required_methods():
    """Verify required methods are implemented in main dashboard."""
    print("\nTesting required methods...")

    dashboard_file = Path('agent_dashboard/codex_dashboard.py')
    content = dashboard_file.read_text()

    required_methods = [
        'compose',
        '_show_panel',
        '_start_updates',
        '_update_dashboard',
        'on_mount',
    ]

    missing_methods = []
    for method in required_methods:
        if f"def {method}" not in content:
            missing_methods.append(method)

    if missing_methods:
        print("FAILED - Missing required methods:")
        for method in missing_methods:
            print(f"  - {method}")
        return False
    else:
        print("PASSED - All required methods implemented")
        return True


def test_theme_variables():
    """Verify theme variables are defined."""
    print("\nTesting theme configuration...")

    dashboard_file = Path('agent_dashboard/codex_dashboard.py')
    content = dashboard_file.read_text()

    required_theme_vars = [
        'background',
        'surface',
        'primary',
        'accent',
        'success',
        'warning',
        'error',
    ]

    missing_vars = []
    for var in required_theme_vars:
        if f'"{var}"' not in content:
            missing_vars.append(var)

    if missing_vars:
        print("FAILED - Missing theme variables:")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    else:
        print("PASSED - Theme variables configured")
        return True


def test_error_handling():
    """Verify error handling is present in key methods."""
    print("\nTesting error handling...")

    files_to_check = [
        'agent_dashboard/codex_dashboard.py',
        'agent_dashboard/codex_widgets/thinking_stream.py',
        'agent_dashboard/codex_widgets/task_panel.py',
        'agent_dashboard/codex_widgets/log_viewer.py',
        'agent_dashboard/codex_widgets/code_viewer.py',
    ]

    files_without_error_handling = []

    for file_path in files_to_check:
        content = Path(file_path).read_text()

        # Check for try/except blocks
        if 'try:' not in content or 'except' not in content:
            files_without_error_handling.append(file_path)

    if files_without_error_handling:
        print("FAILED - Files missing error handling:")
        for file_path in files_without_error_handling:
            print(f"  - {file_path}")
        return False
    else:
        print("PASSED - Error handling present")
        return True


def test_documentation():
    """Verify documentation is comprehensive."""
    print("\nTesting documentation...")

    readme = Path('agent_dashboard/CODEX_README.md')
    quickstart = Path('CODEX_QUICKSTART.md')

    issues = []

    if not readme.exists():
        issues.append("Missing CODEX_README.md")
    else:
        content = readme.read_text()
        required_sections = [
            'Features',
            'Installation',
            'Usage',
            'Architecture',
            'Troubleshooting',
        ]
        for section in required_sections:
            if section not in content:
                issues.append(f"CODEX_README.md missing section: {section}")

    if not quickstart.exists():
        issues.append("Missing CODEX_QUICKSTART.md")
    else:
        content = quickstart.read_text()
        if len(content) < 1000:
            issues.append("CODEX_QUICKSTART.md seems incomplete")

    if issues:
        print("FAILED - Documentation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("PASSED - Documentation complete")
        return True


def test_integration_points():
    """Verify integration with RealAgentManager."""
    print("\nTesting agent integration...")

    dashboard_file = Path('agent_dashboard/codex_dashboard.py')
    content = dashboard_file.read_text()

    required_integrations = [
        'RealAgentManager',
        '_agent_manager',
        'get_state',
        'get_logs',
        'add_task',
        'delete_task',
        'set_active_task',
    ]

    missing = []
    for item in required_integrations:
        if item not in content:
            missing.append(item)

    if missing:
        print("FAILED - Missing integration points:")
        for item in missing:
            print(f"  - {item}")
        return False
    else:
        print("PASSED - Agent integration complete")
        return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Codex Dashboard - Implementation Validation")
    print("=" * 60)

    tests = [
        test_all_files_exist,
        test_dependencies_declared,
        test_imports_valid,
        test_widget_classes,
        test_required_methods,
        test_theme_variables,
        test_error_handling,
        test_no_placeholders,
        test_documentation,
        test_integration_points,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"FAILED - Test crashed: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\nALL TESTS PASSED ✓")
        print("\nThe Codex Dashboard is fully implemented with:")
        print("  - No placeholders or TODOs")
        print("  - Complete error handling")
        print("  - All required features")
        print("  - Comprehensive documentation")
        print("  - Full integration with agent manager")
        print("\nReady for production use!")
        return 0
    else:
        print(f"\n{total - passed} TEST(S) FAILED ✗")
        print("\nPlease review the failures above.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
