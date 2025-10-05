#!/usr/bin/env python3
from setuptools import setup, find_packages
from pathlib import Path

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
    description="Always-on offline-first coding agent with production gates and TUI",
    author="Dylan Millson",
    url="https://github.com/Millsondylan/Offline_ai_agents",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        "textual",
        "watchdog",
        "requests",
        "keyring",
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
            "agent=agent.cli:main",
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
