"""Shared test setup.

The ``engine/*.py`` plugins are generated artifacts (gitignored), so build them
fresh before the suite runs and expose paths/helpers the tests reuse.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_plugin  # noqa: E402

# Regenerate both plugins (VERSION 0.0) before any test imports them.
build_plugin.main()
