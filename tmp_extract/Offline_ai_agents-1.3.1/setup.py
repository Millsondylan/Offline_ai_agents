#!/usr/bin/env python3
from pathlib import Path

from setuptools import find_packages, setup

# Read version from agent/__init__.py
version_file = Path(__file__).parent / "agent" / "__init__.py"
version = "0.2.0"
for line in version_file.read_text().splitlines():
    if line.startswith("__version__"):
        version = line.split('"')[1]
        break

setup(
    name="agent",
    version=version,
    description="Modern CLI control panel for autonomous AI agents",
    author="Dylan Millson",
    url="https://github.com/Millsondylan/Offline_ai_agents",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        # No external dependencies - uses built-in Python curses
    ],
    extras_require={
        "dev": [
            "ruff",
            "bandit",
            "semgrep",
            "pip-audit",
            "pytest",
            "coverage",
        ],
    },
    entry_points={
        "console_scripts": [
            "agent=agent_dashboard.__main__:main",
        ],
    },
    license="Apache-2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
