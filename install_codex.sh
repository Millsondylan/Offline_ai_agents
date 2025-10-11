#!/bin/bash
# Installation script for Codex Dashboard dependencies

set -e

echo "========================================="
echo "Codex Dashboard - Dependency Installer"
echo "========================================="
echo ""

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python 3.11 or later."
    exit 1
fi

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Check if version is 3.11+
PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "Error: Python 3.11 or later is required. Found $PYTHON_VERSION"
    exit 1
fi

echo "Python version OK!"
echo ""

# Check if pip is available
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo "Error: pip not found. Please install pip for Python 3."
    exit 1
fi

echo "Installing Codex Dashboard dependencies..."
echo ""

# Install dependencies
$PYTHON_CMD -m pip install textual>=0.47.0 rich>=13.7.0 pygments>=2.17.0

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "You can now launch the Codex dashboard with:"
echo ""
echo "  agent --codex"
echo ""
echo "Or directly:"
echo ""
echo "  python3 -m agent_dashboard.codex_dashboard"
echo ""
echo "For more information, see:"
echo "  agent_dashboard/CODEX_README.md"
echo ""
