"""ID generation for Akemi graph nodes.

Replaces node-id-gen.sh with pure Python. Generates deterministic,
kebab-case node IDs from class names, file paths, and arbitrary strings.
"""

from __future__ import annotations

import posixpath
import re

KIND_PREFIX: dict[str, str] = {
    "domain": "dom",
    "module": "mod",
    "file": "file",
    "class": "cls",
    "interface": "iface",
    "function": "fn",
    "api": "api",
    "resource": "res",
    "requirement": "req",
    "adr": "adr",
    "technology": "tech",
    "test": "test",
    "doc": "doc",
    "config": "cfg",
    "epic": "epic",
    "story": "story",
    "task": "task",
    "bug": "bug",
    "capability": "cap",
    "feature": "feat",
    "pi": "pi",
    "iteration": "iter",
    "objective": "obj",
}


def to_kebab(name: str) -> str:
    """Convert PascalCase, camelCase, or snake_case to kebab-case.

    Examples::

        >>> to_kebab('UserService')
        'user-service'
        >>> to_kebab('DataLoaderStep')
        'data-loader-step'
        >>> to_kebab('IAdminService')
        'i-admin-service'
        >>> to_kebab('auth_service')
        'auth-service'
        >>> to_kebab('HTMLParser')
        'html-parser'
        >>> to_kebab('getHTTPResponse')
        'get-http-response'
        >>> to_kebab('already-kebab')
        'already-kebab'
    """
    # Insert hyphen before each uppercase letter that follows a lowercase
    # letter or digit, or before a run of uppercase letters followed by
    # a lowercase letter (to handle acronyms like HTTP -> http).
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", s)
    # Replace underscores and any non-alphanumeric (except hyphens)
    s = s.lower()
    s = re.sub(r"[^a-z0-9-]", "-", s)
    # Collapse multiple hyphens and strip leading/trailing hyphens
    s = re.sub(r"-{2,}", "-", s)
    s = s.strip("-")
    return s


def gen_id(prefix: str, name: str) -> str:
    """Generate a node ID from a prefix and a name.

    Example::

        >>> gen_id('cls', 'UserService')
        'cls-user-service'
    """
    return f"{prefix}-{to_kebab(name)}"


def path_to_id(prefix: str, filepath: str) -> str:
    """Generate a node ID from a prefix and a file path.

    Strips the directory portion, then removes up to two file extensions
    from the right.  Known *compound* extensions (``.test.ts``,
    ``.spec.ts``, ``.d.ts``, etc.) are stripped as one unit so that
    ``auth.test.ts`` collapses to ``auth`` while ``auth.service.ts``
    only loses ``.ts``.

    Examples::

        >>> path_to_id('file', 'src/auth/auth.service.ts')
        'file-auth-service'
        >>> path_to_id('file', 'src/utils/helpers.ts')
        'file-helpers'
        >>> path_to_id('test', 'tests/auth.test.ts')
        'test-auth'
    """
    basename = posixpath.basename(filepath)
    # Try stripping a known compound extension first.
    for compound in _COMPOUND_EXTENSIONS:
        if basename.endswith(compound):
            basename = basename[: -len(compound)]
            return gen_id(prefix, basename)
    # Fall back to stripping a single extension.
    dot = basename.rfind(".")
    if dot > 0:
        basename = basename[:dot]
    return gen_id(prefix, basename)


# Compound file extensions to strip as a single unit.  Must be ordered
# from longest to shortest so that ``.stories.tsx`` matches before
# ``.tsx``.
_COMPOUND_EXTENSIONS: tuple[str, ...] = (
    ".stories.tsx",
    ".stories.ts",
    ".stories.jsx",
    ".stories.js",
    ".module.css",
    ".module.scss",
    ".test.tsx",
    ".test.ts",
    ".test.jsx",
    ".test.js",
    ".spec.tsx",
    ".spec.ts",
    ".spec.jsx",
    ".spec.js",
    ".d.ts",
    ".d.mts",
    ".d.cts",
    ".e2e.ts",
    ".e2e.js",
)


def path_to_module(filepath: str) -> str:
    """Return a module ID from the first directory component of a path.

    Examples::

        >>> path_to_module('src/auth/service.ts')
        'mod-src'
        >>> path_to_module('backend/src/auth/service.ts')
        'mod-backend'
    """
    first = filepath.split("/")[0]
    return f"mod-{first}"


def kind_to_prefix(kind: str) -> str:
    """Map a node kind to its ID prefix.

    Falls back to *kind* itself when no mapping exists (matches shell
    behaviour).

    Example::

        >>> kind_to_prefix('class')
        'cls'
        >>> kind_to_prefix('unknown')
        'unknown'
    """
    return KIND_PREFIX.get(kind, kind)
