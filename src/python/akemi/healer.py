"""Deterministic graph self-healing for Akemi.

Fixes the mechanical validation failures that do not need judgment:
ID mismatches, stale paths for moved files, and deprecation of nodes
whose files are gone. Everything that needs a decision is reported
as MANUAL so an agent or a human can resolve it.

Healing never deletes a node file and never invents relationships.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .node import NodeFile
from .paths import today


# Node kinds whose ``path`` field must point at a real filesystem path.
_PATH_KINDS = frozenset({"file", "class", "function", "test", "doc", "config"})


@dataclass
class HealResult:
    """Structured output from :func:`heal`."""

    fixed: list[str] = field(default_factory=list)
    manual: list[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def manual_count(self) -> int:
        return len(self.manual)

    def report(self) -> str:
        """Format as FIXED/MANUAL lines matching the validator style."""
        title = "=== Akemi Graph Heal (dry run) ===" if self.dry_run \
            else "=== Akemi Graph Heal ==="
        verb = "WOULD" if self.dry_run else "FIXED"
        lines: list[str] = [title, ""]
        for msg in self.fixed:
            lines.append(f"{verb} | {msg}")
        for msg in self.manual:
            lines.append(f"MANUAL| {msg}")
        if not self.fixed and not self.manual:
            lines.append("Nothing to heal: graph is mechanically consistent")
        lines.append("")
        fixed_label = "fixable" if self.dry_run else "fixed"
        lines.append(
            f"=== Results: {len(self.fixed)} {fixed_label}, "
            f"{len(self.manual)} need manual fix ==="
        )
        return "\n".join(lines)


def heal(akemi_dir: str | Path, dry_run: bool = False) -> HealResult:
    """Run all self-healing passes against the Akemi graph.

    Passes, in order:
      1. ID mismatch -- the ``id`` field is rewritten to match the
         filename stem, and every ref in the graph pointing at the old
         ID is rewritten to the new one. Skipped (MANUAL) when the stem
         is already taken by another node.
      2. Stale paths -- a node whose ``path`` no longer exists is
         repointed when exactly one file with the same basename exists
         under the scan roots (a move). With no candidate the node is
         set ``status: deprecated`` (the documented rule for removed
         files). Multiple candidates are reported as MANUAL.
      3. Broken refs -- refs that still point at unknown IDs after the
         rename pass are reported as MANUAL; healing never drops or
         invents a relationship.

    Changed nodes get ``updated`` set to today and the index is rebuilt
    unless *dry_run* is set. :attr:`HealResult.manual_count` can serve
    as a process exit code.
    """
    akemi_dir = Path(akemi_dir)
    project_root = akemi_dir.resolve().parent
    nodes_dir = akemi_dir / "graph" / "nodes"
    result = HealResult(dry_run=dry_run)

    # Parse every node file individually so we can fix per-file issues.
    parsed: dict[Path, NodeFile] = {}
    if nodes_dir.is_dir():
        for yaml_path in sorted(nodes_dir.rglob("*.yaml")):
            try:
                parsed[yaml_path] = NodeFile.from_file(yaml_path)
            except Exception:
                result.manual.append(
                    f"Unparseable node: {yaml_path.relative_to(akemi_dir).as_posix()}"
                )

    changed: set[Path] = set()
    all_ids = {n.id for n in parsed.values() if n.id}

    # ------------------------------------------------------------------
    # 1. ID mismatch: id field must equal the filename stem
    # ------------------------------------------------------------------
    renames: dict[str, str] = {}
    for yaml_path, node in sorted(parsed.items()):
        stem = yaml_path.stem
        if not node.id or node.id == stem:
            continue
        if stem in all_ids:
            result.manual.append(
                f"ID mismatch: {yaml_path.name} has id '{node.id}' but "
                f"'{stem}' is already taken by another node"
            )
            continue
        old_id = node.id
        renames[old_id] = stem
        all_ids.discard(old_id)
        all_ids.add(stem)
        node.id = stem
        changed.add(yaml_path)
        result.fixed.append(
            f"ID mismatch: {yaml_path.name} id '{old_id}' set to '{stem}'"
        )

    # Rewrite refs across the graph for every renamed ID.
    if renames:
        for yaml_path, node in parsed.items():
            for ref in node.refs:
                if ref.to in renames:
                    old = ref.to
                    ref.to = renames[old]
                    changed.add(yaml_path)
                    result.fixed.append(
                        f"Ref retarget: {node.id} --{ref.rel}--> {old} "
                        f"now points to {renames[old]}"
                    )

    # ------------------------------------------------------------------
    # 2. Stale paths: repoint moved files, deprecate removed ones
    # ------------------------------------------------------------------
    inventory = _basename_inventory(akemi_dir, project_root)
    for yaml_path, node in sorted(parsed.items()):
        if node.kind not in _PATH_KINDS:
            continue
        if node.status == "deprecated" or not node.path:
            continue
        if (project_root / node.path).exists():
            continue
        basename = Path(node.path).name
        candidates = inventory.get(basename, [])
        if len(candidates) == 1:
            old_path = node.path
            node.path = candidates[0]
            changed.add(yaml_path)
            result.fixed.append(
                f"Moved path: {node.id} repointed {old_path} -> {candidates[0]}"
            )
        elif len(candidates) == 0:
            node.status = "deprecated"
            changed.add(yaml_path)
            result.fixed.append(
                f"Deprecated: {node.id} (path {node.path} no longer exists)"
            )
        else:
            result.manual.append(
                f"Stale path: {node.id} points to {node.path}; "
                f"{len(candidates)} files named {basename} exist, pick one"
            )

    # ------------------------------------------------------------------
    # 3. Broken refs that survive the rename pass need a human or agent
    # ------------------------------------------------------------------
    for yaml_path, node in sorted(parsed.items()):
        for ref in node.refs:
            if ref.to and ref.to not in all_ids:
                result.manual.append(
                    f"Broken ref: {node.id} --{ref.rel}--> {ref.to} "
                    "(no such node; fix the target or create it)"
                )

    # ------------------------------------------------------------------
    # Persist changes and rebuild the index
    # ------------------------------------------------------------------
    if not dry_run and changed:
        for yaml_path in sorted(changed):
            node = parsed[yaml_path]
            node.updated = today()
            try:
                node.to_file(yaml_path)
            except ValueError as exc:
                result.manual.append(f"Write failed: {exc}")
        from .index_builder import build_index
        build_index(akemi_dir)

    return result


def _basename_inventory(
    akemi_dir: Path,
    project_root: Path,
) -> dict[str, list[str]]:
    """Map source file basenames to project-relative paths.

    Uses the same scan roots as the validator so move detection only
    considers files the graph is expected to track.
    """
    from .validator import scan_roots, EXCLUDE_DIRS, EXCLUDE_FILES

    inventory: dict[str, list[str]] = {}
    for root_path, exts in scan_roots(akemi_dir, project_root):
        if not root_path.is_dir():
            continue
        for source_file in sorted(root_path.rglob("*")):
            if not source_file.is_file():
                continue
            if EXCLUDE_DIRS & set(source_file.parts):
                continue
            if source_file.name in EXCLUDE_FILES:
                continue
            if source_file.suffix not in exts:
                continue
            rel = source_file.relative_to(project_root).as_posix()
            inventory.setdefault(source_file.name, []).append(rel)
    return inventory
