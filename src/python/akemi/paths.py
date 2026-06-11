"""Path utilities for Akemi scripts.

Replaces path-utils.sh with pure Python. Provides language-aware
file extension mapping, source/test directory discovery, and
timestamp helpers.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Language mappings
# ---------------------------------------------------------------------------

_LANG_EXT: dict[str, str] = {
    "typescript": "ts",
    "javascript": "js",
    "python": "py",
    "go": "go",
    "rust": "rs",
    "java": "java",
    "scala": "scala",
    "kotlin": "kt",
    "csharp": "cs",
}

# Languages that have additional file extensions beyond the primary one.
_LANG_EXTRA_EXT: dict[str, list[str]] = {
    "typescript": ["tsx"],
    "javascript": ["jsx"],
    "scala": ["sc"],
}

_TEST_PATTERN: dict[str, str] = {
    "typescript": "*.test.ts",  # test_all_patterns adds *.test.tsx
    "javascript": "*.test.js",  # test_all_patterns adds *.test.jsx
    "python": "test_*.py",
    "go": "*_test.go",
    "rust": "*.rs",  # tests are inline in Rust
    "java": "*Test.java",  # test_all_patterns adds *Tests.java
    "scala": "*Spec.scala",  # test_all_patterns adds *Test.scala, *Suite.scala
    "kotlin": "*Test.kt",
    "csharp": "*Tests.cs",
}

# Extra test glob patterns beyond the primary one in _TEST_PATTERN.
_TEST_EXTRA_PATTERNS: dict[str, list[str]] = {
    "typescript": ["*.test.tsx"],
    "javascript": ["*.test.jsx"],
    "java": ["*Tests.java"],
    "scala": ["*Test.scala", "*Suite.scala"],
}

# File extensions recognised as source code (used by validator).
SOURCE_EXTENSIONS: frozenset[str] = frozenset(
    [f".{ext}" for ext in _LANG_EXT.values()]
    + [f".{ext}" for exts in _LANG_EXTRA_EXT.values() for ext in exts]
)

# Directories conventionally containing application source code.
_SOURCE_DIR_NAMES: tuple[str, ...] = (
    "src",
    "app",
    "lib",
    "pkg",
    "cmd",
    "internal",
    "backend",
    "frontend",
    "server",
    "api",
    "services",
    "mcp-server",
    "scripts",
)

# Directories conventionally containing tests.
_TEST_DIR_NAMES: tuple[str, ...] = (
    "tests",
    "test",
    "__tests__",
    "spec",
)

# Maven/Gradle/sbt standard layout (java and scala). When these exist
# they replace the generic "src" entry so that test sources under
# src/test are not scanned as application source.
_JVM_SOURCE_DIR_NAMES: tuple[str, ...] = (
    "src/main/java",
    "src/main/scala",
)

_JVM_TEST_DIR_NAMES: tuple[str, ...] = (
    "src/test/java",
    "src/test/scala",
)

# Subset of source dirs used when scoping to a workspace.
_WS_SOURCE_DIR_NAMES: tuple[str, ...] = (
    "src",
    "app",
    "lib",
    "pkg",
    "cmd",
    "internal",
    "server",
    "api",
    "services",
    "scripts",
)


def lang_ext(lang: str) -> str:
    """Map a language name to its conventional file extension.

    Returns ``'txt'`` for unrecognised languages.

    Example::

        >>> lang_ext('typescript')
        'ts'
        >>> lang_ext('python')
        'py'
    """
    return _LANG_EXT.get(lang, "txt")


def lang_all_ext(lang: str) -> list[str]:
    """Return all file extensions for a language (primary + extras).

    Example::

        >>> lang_all_ext('typescript')
        ['ts', 'tsx']
        >>> lang_all_ext('python')
        ['py']
    """
    primary = _LANG_EXT.get(lang, "txt")
    extras = _LANG_EXTRA_EXT.get(lang, [])
    return [primary] + extras


def test_pattern(lang: str) -> str:
    """Map a language name to a glob pattern matching its test files.

    Returns ``'*.test.*'`` for unrecognised languages.

    Example::

        >>> test_pattern('python')
        'test_*.py'
        >>> test_pattern('typescript')
        '*.test.ts'
    """
    return _TEST_PATTERN.get(lang, "*.test.*")


def test_all_patterns(lang: str) -> list[str]:
    """Return all test glob patterns for a language (primary + extras).

    Example::

        >>> test_all_patterns('typescript')
        ['*.test.ts', '*.test.tsx']
        >>> test_all_patterns('java')
        ['*Test.java', '*Tests.java']
        >>> test_all_patterns('python')
        ['test_*.py']
    """
    return [test_pattern(lang)] + _TEST_EXTRA_PATTERNS.get(lang, [])


def source_dirs(root: str = ".") -> list[str]:
    """Return the subset of standard source directory names that exist
    under *root*.

    Does **not** fall back to ``'.'`` when nothing matches (mirrors the
    shell implementation).

    JVM Maven layout (``src/main/java`` / ``src/main/scala``) takes the
    place of the generic ``src`` entry when present.
    """
    base = Path(root)
    jvm = [d for d in _JVM_SOURCE_DIR_NAMES if (base / d).is_dir()]
    dirs = [d for d in _SOURCE_DIR_NAMES if (base / d).is_dir()]
    if jvm:
        dirs = jvm + [d for d in dirs if d != "src"]
    return dirs


def test_dirs(root: str = ".") -> list[str]:
    """Return the subset of standard test directory names that exist
    under *root*.

    Includes JVM Maven layout test roots (``src/test/java`` /
    ``src/test/scala``) when present.
    """
    base = Path(root)
    jvm = [d for d in _JVM_TEST_DIR_NAMES if (base / d).is_dir()]
    return jvm + [d for d in _TEST_DIR_NAMES if (base / d).is_dir()]


def workspace_source_dirs(ws_root: str) -> list[str]:
    """Source directories scoped to a workspace root.

    If none of the standard sub-directories exist, returns ``[ws_root]``
    so the caller always has at least one directory to scan.

    JVM Maven layout roots replace the generic ``src`` entry when present.
    """
    base = Path(ws_root)
    jvm = [str(base / d) for d in _JVM_SOURCE_DIR_NAMES if (base / d).is_dir()]
    dirs = [str(base / d) for d in _WS_SOURCE_DIR_NAMES if (base / d).is_dir()]
    if jvm:
        dirs = jvm + [d for d in dirs if d != str(base / "src")]
    if not dirs:
        dirs = [ws_root]
    return dirs


def workspace_test_dirs(ws_root: str) -> list[str]:
    """Test directories scoped to a workspace root.

    Also checks for ``tests/<ws_name>/`` and ``test/<ws_name>/`` at the
    project root (matching the shell implementation).
    """
    base = Path(ws_root)
    dirs = [str(base / d) for d in _JVM_TEST_DIR_NAMES if (base / d).is_dir()]
    dirs += [str(base / d) for d in _TEST_DIR_NAMES if (base / d).is_dir()]

    # Derive workspace name from the root path (strip trailing slash).
    ws_name = os.path.basename(ws_root.rstrip("/").rstrip("\\"))
    for test_dir in ("tests", "test"):
        candidate = Path(test_dir) / ws_name
        if candidate.is_dir():
            dirs.append(str(candidate))

    return dirs


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------


def today() -> str:
    """Return today's date as ``YYYY-MM-DD``."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_iso() -> str:
    """Return the current UTC time in ISO 8601 format.

    Example: ``2026-04-01T12:00:00Z``
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
