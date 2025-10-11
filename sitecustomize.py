"""Ensure the repository root is always importable when running tests."""

import os
import sys

ROOT = os.path.dirname(__file__)
if ROOT and ROOT not in sys.path:
    sys.path.insert(0, ROOT)

