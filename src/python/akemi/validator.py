"""Graph integrity checks for Akemi.

Replaces validate.sh with pure Python.  Runs nine validation checks
against the node files, journey files, and the source tree, producing
structured results matching the bash output format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import yaml_io

from .config import AkemiConfig
from .node import NodeFile, read_all_nodes
from .paths import SOURCE_EXTENSIONS, lang_ext


@dataclass
class ValidationResult:
    """Structured output from :func:`validate`."""

    passes: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.failures)

    def report(self) -> str:
        """Format as PASS/FAIL/WARN lines matching bash output format.

        Example::

            === Akemi Graph Validation ===

            PASS  | Broken references: 0 found
            FAIL  | Over limit: cls-foo has 135 lines (max 120)
            WARN  | Stale path: file-bar points to src/bar.ts (not found)

            === Results: 1 errors, 1 warnings ===
        """
        lines: list[str] = [
            "=== Akemi Graph Validation ===",
            "",
        ]
        for msg in self.passes:
            lines.append(f"PASS  | {msg}")
        for msg in self.failures:
            lines.append(f"FAIL  | {msg}")
        for msg in self.warnings:
            lines.append(f"WARN  | {msg}")
        lines.append("")
        lines.append(
            f"=== Results: {len(self.failures)} errors, "
            f"{len(self.warnings)} warnings ==="
        )
        return "\n".join(lines)


def validate(akemi_dir: str | Path) -> ValidationResult:
    """Run all integrity checks against the Akemi graph.

    Checks performed:
      1. Broken references -- all ``refs[].to`` must point to existing node IDs.
      2. Line count -- no node file over 120 lines.
      3. ID consistency -- filename (without ``.yaml``) must match ``id`` field.
      4. Stale paths -- file/class/function/test/doc/config nodes with a
         ``path`` value must point to an existing filesystem path
         (skip if status is ``deprecated``).
      5. Missing source nodes -- source files under workspace roots
         (or ``src/`` for single-project repos) without a
         corresponding graph node.
      6. Test coverage -- all non-deprecated class and function nodes
         should have a test node with a ``tests`` ref pointing to them.
      7. Orphan nodes -- nodes with no incoming or outgoing edges
         (warning only).
      8. Journey refs -- all ``graph_refs`` in journey YAML files must
         reference existing node IDs.
      9. SAFe hierarchy -- stories should realize a feature or epic,
         features should realize a capability or epic, and iterations
         should be part_of a PI (warnings only; skipped when the graph
         has no feature/story/pi nodes).

    Returns a :class:`ValidationResult` whose :attr:`error_count` can
    serve as a process exit code.
    """
    akemi_dir = Path(akemi_dir)
    # Node paths are relative to the project root, not the CWD
    project_root = akemi_dir.resolve().parent
    nodes_dir = akemi_dir / "graph" / "nodes"
    result = ValidationResult()

    nodes = read_all_nodes(nodes_dir)
    all_ids = set(nodes.keys())

    # Also build a mapping from yaml filename stem -> file path so we
    # can check ID consistency per-file.
    file_stem_to_path: dict[str, Path] = {}
    if nodes_dir.is_dir():
        for yaml_path in sorted(nodes_dir.rglob("*.yaml")):
            file_stem_to_path[yaml_path.stem] = yaml_path

    # ------------------------------------------------------------------
    # 1. Broken references
    # ------------------------------------------------------------------
    broken_count = 0
    for nid, node in sorted(nodes.items()):
        for ref in node.refs:
            if not ref.to:
                continue
            if ref.to not in all_ids:
                result.failures.append(
                    f"Broken ref: {nid} --{ref.rel}--> {ref.to} (target not found)"
                )
                broken_count += 1

    if broken_count == 0:
        result.passes.append("Broken references: 0 found")

    # ------------------------------------------------------------------
    # 2. Line count
    # ------------------------------------------------------------------
    over_limit = 0
    for yaml_path in sorted(nodes_dir.rglob("*.yaml")) if nodes_dir.is_dir() else []:
        try:
            line_count = yaml_path.read_text(encoding="utf-8").count("\n") + 1
        except OSError:
            continue

        # Resolve the node ID from the file stem.
        nid = yaml_path.stem
        if line_count > 120:
            result.failures.append(
                f"Over limit: {nid} has {line_count} lines (max 120)"
            )
            over_limit += 1

    if over_limit == 0:
        result.passes.append("Line count: all nodes under 120 lines")

    # ------------------------------------------------------------------
    # 3. ID consistency
    # ------------------------------------------------------------------
    id_mismatches = 0
    for yaml_path in sorted(nodes_dir.rglob("*.yaml")) if nodes_dir.is_dir() else []:
        stem = yaml_path.stem
        if stem not in nodes:
            # File could not be parsed; skip.
            continue
        node = nodes[stem]
        if node.id != stem:
            result.failures.append(
                f"ID mismatch: file {yaml_path.name} has id '{node.id}'"
            )
            id_mismatches += 1

    if id_mismatches == 0:
        result.passes.append("ID consistency: all IDs match filenames")

    # ------------------------------------------------------------------
    # 4. Stale paths
    # ------------------------------------------------------------------
    _STALE_KINDS = frozenset({"file", "class", "function", "test", "doc", "config"})
    stale_count = 0
    for nid, node in sorted(nodes.items()):
        if node.kind not in _STALE_KINDS:
            continue
        if node.status == "deprecated":
            continue
        if not node.path:
            continue
        if not (project_root / node.path).exists():
            result.warnings.append(
                f"Stale path: {nid} points to {node.path} (not found)"
            )
            stale_count += 1

    if stale_count == 0:
        result.passes.append("Stale paths: all paths valid")

    # ------------------------------------------------------------------
    # 5. Missing source nodes (workspace-aware)
    # ------------------------------------------------------------------
    # Collect all declared paths from file, class, function, and test nodes.
    declared_paths: set[str] = set()
    _PATH_KINDS = frozenset({"file", "class", "function", "test"})
    for node in nodes.values():
        if node.kind in _PATH_KINDS and node.path:
            declared_paths.add(node.path)

    # Directories and files to exclude when scanning workspace roots.
    _EXCLUDE_DIRS = frozenset({
        "__pycache__", "node_modules", ".next", "dist", "build",
        ".venv", "venv", ".git", ".mypy_cache", ".pytest_cache",
        "egg-info",
    })
    _EXCLUDE_FILES = frozenset({"__init__.py", "conftest.py"})

    # Determine scan roots: read workspace config if available,
    # otherwise fall back to src/ for single-project repos.
    config_path = akemi_dir / "akemi.yaml"
    scan_roots: list[tuple[Path, frozenset[str]]] = []

    if config_path.is_file():
        cfg = AkemiConfig.from_file(config_path)
        if cfg.is_monorepo and cfg.workspaces:
            for ws_name, ws_cfg in cfg.workspaces.items():
                ws_root = project_root / ws_cfg.root
                # Build the set of extensions for this workspace's language.
                ext = lang_ext(ws_cfg.language)
                if ws_cfg.language == "typescript":
                    ws_exts = frozenset({".ts", ".tsx"})
                elif ws_cfg.language == "javascript":
                    ws_exts = frozenset({".js", ".jsx"})
                else:
                    ws_exts = frozenset({f".{ext}"})
                scan_roots.append((ws_root, ws_exts))

    # Fallback for single-project repos.
    if not scan_roots:
        src_dir = project_root / "src"
        if src_dir.is_dir():
            scan_roots.append((src_dir, SOURCE_EXTENSIONS))

    missing_count = 0
    for root_path, exts in scan_roots:
        if not root_path.is_dir():
            continue
        for source_file in sorted(root_path.rglob("*")):
            if not source_file.is_file():
                continue
            # Skip excluded directories anywhere in the path.
            if _EXCLUDE_DIRS & set(source_file.parts):
                continue
            # Skip excluded filenames.
            if source_file.name in _EXCLUDE_FILES:
                continue
            if source_file.suffix not in exts:
                continue
            # Declared node paths are relative to the project root
            rel_path = source_file.relative_to(project_root).as_posix()
            if rel_path not in declared_paths:
                result.warnings.append(
                    f"Missing node: {rel_path} has no graph node"
                )
                missing_count += 1

    if missing_count == 0:
        result.passes.append(
            "Missing nodes: all source files have graph nodes"
        )

    # ------------------------------------------------------------------
    # 6. Test coverage
    # ------------------------------------------------------------------
    # Collect all entity IDs that are referenced by a test node's
    # ``tests`` relationship.
    tested_ids: set[str] = set()
    for node in nodes.values():
        if node.kind == "test":
            for ref in node.refs:
                if ref.rel == "tests":
                    tested_ids.add(ref.to)

    # Tags that exempt a node from needing test coverage (data-only classes).
    _TEST_EXEMPT_TAGS = frozenset({"dto", "model"})

    untested_count = 0
    for nid, node in sorted(nodes.items()):
        if node.kind not in ("class", "function"):
            continue
        if node.status == "deprecated":
            continue
        if _TEST_EXEMPT_TAGS & set(node.tags):
            continue
        if nid not in tested_ids:
            result.warnings.append(f"No test coverage: {nid}")
            untested_count += 1

    if untested_count == 0:
        result.passes.append(
            "Test coverage: all classes/functions have tests"
        )

    # ------------------------------------------------------------------
    # 7. Orphan nodes
    # ------------------------------------------------------------------
    # A node is an orphan if it has no incoming AND no outgoing edges.
    nodes_with_outgoing: set[str] = set()
    nodes_with_incoming: set[str] = set()

    for node in nodes.values():
        for ref in node.refs:
            if ref.rel and ref.to:
                nodes_with_outgoing.add(node.id)
                nodes_with_incoming.add(ref.to)

    orphan_count = 0
    for nid in sorted(all_ids):
        if nid not in nodes_with_outgoing and nid not in nodes_with_incoming:
            result.warnings.append(f"Orphan node: {nid} (no edges)")
            orphan_count += 1

    if orphan_count == 0:
        result.passes.append("Orphan nodes: none found")

    # ------------------------------------------------------------------
    # 8. Journey ref validation
    # ------------------------------------------------------------------
    _check_journey_refs(akemi_dir, all_ids, result)

    # ------------------------------------------------------------------
    # 9. SAFe hierarchy (warnings only, never failures)
    # ------------------------------------------------------------------
    _check_safe_hierarchy(nodes, result)

    return result


# Maps a work-item kind to its ID prefix, used to resolve refs whose
# target node file does not exist yet (broken refs are already flagged
# by check 1).
_SAFE_PREFIX: dict[str, str] = {
    "epic": "epic",
    "capability": "cap",
    "feature": "feat",
    "pi": "pi",
}


def _check_safe_hierarchy(
    nodes: dict[str, NodeFile],
    result: ValidationResult,
) -> None:
    """Check 9: SAFe work-item hierarchy (warnings only).

    Skipped entirely when the graph has no feature/story/pi nodes so
    plain code-graphs stay clean.
    """
    has_work_items = any(
        n.kind in ("feature", "story", "pi") for n in nodes.values()
    )
    if not has_work_items:
        result.passes.append("SAFe hierarchy: no work items found (skipped)")
        return

    def _has_ref_to_kind(node: NodeFile, rel: str, kinds: tuple[str, ...]) -> bool:
        for ref in node.refs:
            if ref.rel != rel or not ref.to:
                continue
            target = nodes.get(ref.to)
            if target is not None:
                if target.kind in kinds:
                    return True
                continue
            # Target node missing: fall back to ID prefix matching.
            prefix = ref.to.split("-", 1)[0]
            if any(_SAFE_PREFIX[k] == prefix for k in kinds):
                return True
        return False

    warn_count = 0
    for nid, node in sorted(nodes.items()):
        if node.kind == "story":
            if not _has_ref_to_kind(node, "realizes", ("feature", "epic")):
                result.warnings.append(
                    f"SAFe hierarchy: {nid} has no realizes ref to a feature or epic"
                )
                warn_count += 1
        elif node.kind == "feature":
            if not _has_ref_to_kind(node, "realizes", ("capability", "epic")):
                result.warnings.append(
                    f"SAFe hierarchy: {nid} has no realizes ref to a capability or epic"
                )
                warn_count += 1
        elif node.kind == "iteration":
            if not _has_ref_to_kind(node, "part_of", ("pi",)):
                result.warnings.append(
                    f"SAFe hierarchy: {nid} has no part_of ref to a pi"
                )
                warn_count += 1

    if warn_count == 0:
        result.passes.append("SAFe hierarchy: all work items linked")


def _check_journey_refs(
    akemi_dir: Path,
    all_ids: set[str],
    result: ValidationResult,
) -> None:
    """Validate all graph_refs in journey YAML files against the graph."""
    journey_dir = akemi_dir / "journeys"
    if not journey_dir.is_dir():
        result.passes.append("Journey refs: no journey files found (skipped)")
        return

    broken = 0
    for journey_file in sorted(journey_dir.glob("journey-*.yaml")):
        try:
            raw = yaml_io.safe_load(journey_file.read_text(encoding="utf-8"))
        except Exception:
            result.warnings.append(f"Journey parse error: {journey_file.name}")
            continue

        if not isinstance(raw, dict):
            result.warnings.append(
                f"Journey parse error: {journey_file.name} (empty or invalid)"
            )
            continue

        jid = raw.get("id", journey_file.stem)

        # States
        for state in raw.get("states") or []:
            sid = state.get("id", "?")
            for ref in state.get("graph_refs") or []:
                if ref not in all_ids:
                    result.failures.append(
                        f"Journey broken ref: {jid} state {sid} -> {ref}"
                    )
                    broken += 1

        # Transitions (trigger + backend_process)
        for trans in raw.get("transitions") or []:
            tid = trans.get("id", "?")
            trigger = trans.get("trigger") or {}
            for ref in trigger.get("graph_refs") or []:
                if ref not in all_ids:
                    result.failures.append(
                        f"Journey broken ref: {jid} transition {tid} trigger -> {ref}"
                    )
                    broken += 1
            bp = trans.get("backend_process") or {}
            for ref in bp.get("graph_refs") or []:
                if ref not in all_ids:
                    result.failures.append(
                        f"Journey broken ref: {jid} transition {tid} backend -> {ref}"
                    )
                    broken += 1

    if broken == 0:
        result.passes.append("Journey refs: all graph_refs valid")
