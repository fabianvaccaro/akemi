"""YAML loading helper.

Uses the libyaml C loader when PyYAML was built with it, which parses
roughly 10x faster. Falls back to the pure-Python safe loader.
"""

from __future__ import annotations

from typing import Any

import yaml

_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def safe_load(text: str) -> Any:
    """Parse YAML text with the fastest available safe loader."""
    return yaml.load(text, Loader=_LOADER)
