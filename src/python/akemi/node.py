"""YAML node file read/write for Akemi graph nodes.

Replaces parse-yaml.sh with proper YAML handling via pyyaml.
Each node file uses YAML frontmatter between ``---`` delimiters
followed by an optional Markdown body.

Format::

    ---
    kind: class
    id: cls-user-service
    name: UserService
    status: active
    tags: [auth, core]
    created: 2026-04-01
    updated: 2026-04-01
    path: src/auth/user-service.ts
    line: 1
    language: typescript
    refs:
      - { rel: part_of, to: file-user-service }
    ---
    Markdown body describing the node.
"""

from __future__ import annotations

import datetime
import re as _re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from . import yaml_io

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

# Known scalar fields that map directly onto NodeFile attributes.
_KNOWN_FIELDS: frozenset[str] = frozenset(
    {
        "akemi",
        "kind",
        "id",
        "name",
        "status",
        "tags",
        "created",
        "updated",
        "path",
        "line",
        "language",
        "refs",
    }
)


@dataclass
class Ref:
    """A typed directed reference from one node to another."""

    rel: str
    to: str

    def to_dict(self) -> dict[str, str]:
        return {"rel": self.rel, "to": self.to}


@dataclass
class NodeFile:
    """In-memory representation of an Akemi node file."""

    kind: str
    id: str
    name: str
    status: str = "active"
    tags: list[str] = field(default_factory=list)
    created: str = ""
    updated: str = ""
    path: str = ""
    line: int = 0
    language: str = ""
    refs: list[Ref] = field(default_factory=list)
    body: str = ""
    # Extra fields not covered above (e.g. pattern, method, pure, loc, ...).
    extra: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, filepath: str | Path) -> "NodeFile":
        """Read a YAML node file (frontmatter between ``---`` delimiters
        plus a Markdown body after the second delimiter)."""
        filepath = Path(filepath)
        raw = filepath.read_text(encoding="utf-8")
        return cls.from_string(raw)

    @classmethod
    def from_string(cls, raw: str) -> "NodeFile":
        """Parse a raw string in frontmatter + body format."""
        frontmatter_str, body = _split_frontmatter(raw)
        data: dict[str, Any] = yaml_io.safe_load(frontmatter_str) or {}
        return cls._from_dict(data, body)

    @classmethod
    def _from_dict(cls, data: dict[str, Any], body: str = "") -> "NodeFile":
        # Extract refs
        raw_refs: list[dict[str, str]] = data.get("refs") or []
        refs = [Ref(rel=r.get("rel", ""), to=r.get("to", "")) for r in raw_refs]

        # Extract tags (could be a list or a YAML string like "[]")
        raw_tags = data.get("tags")
        if isinstance(raw_tags, list):
            tags = [str(t) for t in raw_tags]
        elif isinstance(raw_tags, str):
            tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        else:
            tags = []

        # Collect extra fields
        extra: dict[str, Any] = {}
        for k, v in data.items():
            if k not in _KNOWN_FIELDS:
                extra[k] = v

        return cls(
            kind=str(data.get("kind", "")),
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            status=str(data.get("status", "active")),
            tags=tags,
            created=str(data.get("created", "")),
            updated=str(data.get("updated", "")),
            path=str(data.get("path", "")),
            line=int(data.get("line", 0) or 0),
            language=str(data.get("language", "")),
            refs=refs,
            body=body,
            extra=extra,
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return an ordered dict suitable for YAML serialisation."""
        d: dict[str, Any] = {"akemi": "v1", "kind": self.kind, "id": self.id, "name": self.name}
        d["status"] = self.status
        d["tags"] = self.tags
        if self.created:
            d["created"] = _to_yaml_date(self.created)
        if self.updated:
            d["updated"] = _to_yaml_date(self.updated)
        if self.path:
            d["path"] = self.path
        if self.line:
            d["line"] = self.line
        if self.language:
            d["language"] = self.language
        # Merge extra fields before refs so they appear in a natural order.
        for k, v in self.extra.items():
            d[k] = v
        if self.refs:
            d["refs"] = [r.to_dict() for r in self.refs]
        return d

    def to_file(self, filepath: str | Path) -> None:
        """Write the node file with YAML frontmatter and Markdown body.

        Raises ``ValueError`` if the output would exceed 120 lines
        (the Akemi node line limit).
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        content = self.to_string()
        line_count = content.count("\n") + (0 if content.endswith("\n") else 1)
        if line_count > 120:
            raise ValueError(
                f"Node file would be {line_count} lines (limit is 120): {filepath}"
            )
        filepath.write_text(content, encoding="utf-8")

    def to_string(self) -> str:
        """Serialise to the frontmatter + body string format."""
        fm = yaml.dump(
            self.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=200,
        )
        # Rewrite refs into inline flow style for readability:
        #   - {rel: X, to: Y}
        fm = _inline_refs(fm)

        body = self.body.rstrip("\n")
        if body:
            return f"---\n{fm}---\n{body}\n"
        return f"---\n{fm}---\n"

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def ref_pairs(self) -> list[tuple[str, str]]:
        """Return refs as ``(rel, target)`` tuples."""
        return [(r.rel, r.to) for r in self.refs]


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def read_all_nodes(nodes_dir: str | Path) -> dict[str, NodeFile]:
    """Recursively read all ``.yaml`` files under *nodes_dir*.

    Returns a dict keyed by node ``id``.
    """
    nodes_dir = Path(nodes_dir)
    result: dict[str, NodeFile] = {}
    if not nodes_dir.is_dir():
        return result
    for yaml_path in sorted(nodes_dir.rglob("*.yaml")):
        try:
            node = NodeFile.from_file(yaml_path)
        except Exception:
            # Skip files that fail to parse (e.g. index.yaml).
            continue
        if node.id:
            result[node.id] = node
    return result


def write_node_if_new(nodes_dir: str | Path, node: NodeFile) -> bool:
    """Write a node file only if a file for this ID does not already exist.

    The file is placed at ``<nodes_dir>/<kind>/<id>.yaml``.
    Returns ``True`` if the file was written, ``False`` if it already
    existed.
    """
    nodes_dir = Path(nodes_dir)
    target = nodes_dir / node.kind / f"{node.id}.yaml"
    if target.exists():
        return False
    node.to_file(target)
    return True


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _split_frontmatter(raw: str) -> tuple[str, str]:
    """Split a ``---`` delimited document into (frontmatter, body).

    The first line must be ``---``. The frontmatter extends until the
    next ``---`` line. Everything after that second delimiter is the
    body.
    """
    lines = raw.split("\n")

    # Find the opening delimiter.
    start = -1
    for i, line in enumerate(lines):
        if line.strip() == "---":
            start = i
            break

    if start == -1:
        # No frontmatter delimiter at all -- treat entire content as
        # body with empty frontmatter.
        return ("", raw)

    # Find the closing delimiter.
    end = -1
    for i in range(start + 1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break

    if end == -1:
        # Only one delimiter -- treat everything after it as
        # frontmatter with no body (best-effort).
        return ("\n".join(lines[start + 1 :]), "")

    frontmatter = "\n".join(lines[start + 1 : end])
    body = "\n".join(lines[end + 1 :]).strip("\n")
    return (frontmatter, body)


def _inline_refs(yaml_str: str) -> str:
    """Rewrite the multi-line ``refs:`` block emitted by pyyaml into
    compact inline form: ``- {rel: X, to: Y}``

    pyyaml's ``default_flow_style=False`` renders each ref dict across
    multiple lines.  This function collapses each ref back to a single
    line for readability and to keep files short.

    Only transforms list items that appear after a ``refs:`` line, so
    other list-of-dict fields are left untouched.
    """
    output_lines: list[str] = []
    lines = yaml_str.split("\n")
    i = 0
    in_refs = False
    while i < len(lines):
        line = lines[i]

        # Track when we enter/leave the refs block.
        if line.rstrip() == "refs:":
            in_refs = True
            output_lines.append(line)
            i += 1
            continue

        if in_refs:
            # pyyaml default: list items at same indent as parent key
            # "- rel: part_of"
            # "  to: file-x"
            if line.startswith("- rel: ") and i + 1 < len(lines) and lines[i + 1].startswith("  to: "):
                rel_val = line[len("- rel: "):].strip()
                to_val = lines[i + 1][len("  to: "):].strip()
                output_lines.append(f"  - {{rel: {rel_val}, to: {to_val}}}")
                i += 2
                continue
            # pyyaml with indent=2: list items indented under parent
            # "  - rel: part_of"
            # "    to: file-x"
            if line.startswith("  - rel: ") and i + 1 < len(lines) and lines[i + 1].startswith("    to: "):
                rel_val = line[len("  - rel: "):].strip()
                to_val = lines[i + 1][len("    to: "):].strip()
                output_lines.append(f"  - {{rel: {rel_val}, to: {to_val}}}")
                i += 2
                continue
            # If we hit a line that is not a continuation of the refs
            # list (not blank, not starting with - or whitespace), we
            # have left the refs block.
            if line and not line.startswith((" ", "-")):
                in_refs = False

        output_lines.append(line)
        i += 1
    return "\n".join(output_lines)


_DATE_RE = _re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _to_yaml_date(value: str) -> datetime.date | str:
    """Convert a ``YYYY-MM-DD`` string to a :class:`datetime.date` so
    that pyyaml serialises it without quotes.  Returns the original
    string unchanged if it does not match the date pattern."""
    if _DATE_RE.match(value):
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            pass
    return value
