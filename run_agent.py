#!/usr/bin/env python3
"""Fixed agent runner that works correctly."""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_dashboard.__main__ import run_real_agent

if __name__ == "__main__":
    run_real_agent()