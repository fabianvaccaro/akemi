"""Main orchestrator: detect project, scan sources, create graph nodes.

Replaces bootstrap.sh (291 lines of bash) with a single Python module.
Drives the full bootstrap pipeline: detection, scanning, node creation,
index rebuild, and view generation.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from .config import AkemiConfig, WorkspaceConfig
from .detector import DetectionResult, detect, detect_workspaces
from .id_gen import gen_id, path_to_id, path_to_module, to_kebab
from .index_builder import build_index
from .node import NodeFile, Ref, write_node_if_new
from .paths import (
    lang_ext,
    now_iso,
    source_dirs,
    test_dirs,
    test_pattern,
    today,
    workspace_source_dirs,
    workspace_test_dirs,
)
from .scanner import ClassDef, resolve_refs, scan_file
from .view_generator import rebuild_views


# Directories excluded from recursive file discovery.
_EXCLUDE_DIRS: frozenset[str] = frozenset({
    "node_modules", ".next", "dist", ".git", "__pycache__",
    "venv", ".venv", ".akemi",
})

# Config files to scan and the config_type assigned to each.
_CONFIG_FILES: tuple[tuple[str, str], ...] = (
    ("Dockerfile", "docker"),
    ("docker-compose.yml", "docker"),
    ("docker-compose.yaml", "docker"),
    (".env.example", "environment"),
    (".env.production", "environment"),
    ("Makefile", "build"),
)

# Minimum line count for creating *file* nodes (class scanning has no minimum).
_FILE_NODE_MIN_LINES: int = 20


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_bootstrap(project_root: str = ".", depth: str = "tier2") -> None:
    """Full bootstrap: detect -> scan -> create nodes -> index -> views.

    Parameters
    ----------
    project_root:
        Root directory of the project to bootstrap.  Defaults to the
        current working directory.
    depth:
        ``'tier1'`` creates technology and module nodes only.
        ``'tier2'`` (default) additionally scans source files for classes,
        interfaces, file nodes, and test nodes.
    """
    root = Path(project_root).resolve()
    akemi_dir = root / ".akemi"
    nodes_dir = akemi_dir / "graph" / "nodes"
    config_path = akemi_dir / "akemi.yaml"
    date = today()
    node_count = 0

    _info(f"==> Bootstrapping Akemi graph (depth: {depth})")
    _info("  Detecting project structure...")

    project_info = detect_workspaces(str(root))

    # ------------------------------------------------------------------ #
    # Monorepo
    # ------------------------------------------------------------------ #
    if project_info.type == "monorepo":
        _info("  Monorepo detected. Bootstrapping workspaces...")

        for ws in project_info.workspaces:
            ws_root = str(root / ws.root.rstrip("/"))
            created = _bootstrap_workspace(
                ws_name=ws.name,
                ws_root=ws_root,
                detection=ws.detection,
                nodes_dir=nodes_dir,
                project_root=root,
                date=date,
                depth=depth,
            )
            node_count += created

        # Update akemi.yaml
        if config_path.is_file():
            cfg = AkemiConfig.from_file(config_path)
        else:
            cfg = AkemiConfig()

        cfg.name = root.name
        cfg.type = "monorepo"
        cfg.language = ""
        cfg.framework = ""
        cfg.test_framework = ""
        cfg.package_manager = ""
        cfg.workspaces = {
            ws.name: WorkspaceConfig(
                root=ws.root,
                language=ws.detection.language,
                framework=ws.detection.framework,
                test_framework=ws.detection.test_framework,
                package_manager=ws.detection.package_manager,
            )
            for ws in project_info.workspaces
        }
        cfg.to_file(config_path)

    # ------------------------------------------------------------------ #
    # Single project
    # ------------------------------------------------------------------ #
    else:
        det = project_info.detection
        _info(f"  Language: {det.language}, Framework: {det.framework}")

        created = _bootstrap_workspace(
            ws_name="default",
            ws_root=str(root),
            detection=det,
            nodes_dir=nodes_dir,
            project_root=root,
            date=date,
            depth=depth,
        )
        node_count += created

        # Update akemi.yaml
        if config_path.is_file():
            cfg = AkemiConfig.from_file(config_path)
        else:
            cfg = AkemiConfig()

        cfg.name = root.name
        cfg.type = "single"
        cfg.language = det.language
        cfg.framework = det.framework
        cfg.test_framework = det.test_framework
        cfg.package_manager = det.package_manager
        cfg.workspaces = {}
        cfg.to_file(config_path)

    # ------------------------------------------------------------------ #
    # Config nodes (shared, not workspace-specific)
    # ------------------------------------------------------------------ #
    _info("  Scanning config files...")
    node_count += _create_config_nodes(root, nodes_dir, date)

    # ------------------------------------------------------------------ #
    # Rebuild index and views
    # ------------------------------------------------------------------ #
    _info("  Building index...")
    try:
        index_msg = build_index(str(akemi_dir))
        _info(index_msg)
    except FileNotFoundError:
        _info("  (skipped index - no nodes directory)")

    _info("  Building views...")
    try:
        views_msg = rebuild_views(str(akemi_dir))
        _info(views_msg)
    except FileNotFoundError:
        _info("  (skipped views - no nodes directory)")

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    _info("")
    _info(f"==> Bootstrap complete: {node_count} nodes created")
    _info(f"    Graph: {akemi_dir / 'graph'}/")
    _info(f"    Index: {akemi_dir / 'graph' / 'index.yaml'}")


# ---------------------------------------------------------------------------
# Workspace bootstrap
# ---------------------------------------------------------------------------


def _bootstrap_workspace(
    *,
    ws_name: str,
    ws_root: str,
    detection: DetectionResult,
    nodes_dir: Path,
    project_root: Path,
    date: str,
    depth: str,
) -> int:
    """Bootstrap a single workspace (or the full project for single-mode).

    Returns the number of new nodes written.
    """
    lang = detection.language
    framework = detection.framework
    test_fw = detection.test_framework

    if lang == "unknown":
        _info(f"  [{ws_name}] No language detected - skipping.")
        return 0

    _info(f"  [{ws_name}] Language: {lang}, Framework: {framework}")

    count = 0

    # ---- Technology nodes ----
    count += _write(nodes_dir, _tech_node(lang, "language", date))
    if framework != "unknown":
        count += _write(nodes_dir, _tech_node(framework, "framework", date))
    if test_fw != "unknown":
        count += _write(nodes_dir, _tech_node(test_fw, "testing", date))

    # ---- Module nodes ----
    ws_root_path = Path(ws_root)
    is_project_root = ws_root_path == project_root

    if is_project_root:
        src_roots = [str(project_root / d) for d in source_dirs(str(project_root))]
    else:
        src_roots = workspace_source_dirs(ws_root)

    for src_root in src_roots:
        src_path = Path(src_root)
        if not src_path.is_dir():
            continue
        for child in sorted(src_path.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith(".") or child.name in _EXCLUDE_DIRS:
                continue
            mod_name = child.name
            mod_id = f"mod-{mod_name}"
            mod_node = NodeFile(
                kind="module",
                id=mod_id,
                name=mod_name,
                status="active",
                created=date,
                updated=date,
                path=f"{_relpath(child, project_root)}/",
                language=lang,
                refs=[Ref(rel="uses_technology", to=f"tech-{lang}")],
                extra={"visibility": "public"},
            )
            count += _write(nodes_dir, mod_node)

    # ---- Tier 2: file, class/interface, test nodes ----
    if depth == "tier2":
        count += _tier2_scan(
            ws_name=ws_name,
            ws_root=ws_root,
            lang=lang,
            test_fw=test_fw,
            src_roots=src_roots,
            nodes_dir=nodes_dir,
            project_root=project_root,
            date=date,
            is_project_root=is_project_root,
        )

    return count


# ---------------------------------------------------------------------------
# Tier 2 scanning
# ---------------------------------------------------------------------------


def _tier2_scan(
    *,
    ws_name: str,
    ws_root: str,
    lang: str,
    test_fw: str,
    src_roots: list[str],
    nodes_dir: Path,
    project_root: Path,
    date: str,
    is_project_root: bool,
) -> int:
    """Scan source files for classes/interfaces and create file/class/test nodes.

    Returns the number of new nodes written.
    """
    count = 0
    ext = lang_ext(lang)
    glob_pattern = f"*.{ext}"

    # Collect all discovered ClassDefs across source roots for resolution.
    all_class_defs: list[ClassDef] = []

    # Track which file nodes exist so class part_of refs never point to
    # file nodes skipped by the line threshold (would fail validation).
    file_ids_with_nodes: set[str] = set()
    module_by_rel: dict[str, str] = {}

    # ---- Source file scanning ----
    for src_root in src_roots:
        src_path = Path(src_root)
        if not src_path.is_dir():
            continue

        for filepath in _rglob_safe(src_path, glob_pattern):
            rel = _relpath(filepath, project_root)

            # Scan every file for classes (no line minimum).
            defs = _scan_safe(filepath, lang)
            all_class_defs.extend(defs)

            # Compute parent module relative to source root (aligns with module node creation)
            rel_to_src = _relpath(filepath, src_path)
            module_by_rel[rel] = path_to_module(rel_to_src)

            # Only create file nodes for files with enough lines.
            line_count = _count_lines(filepath)
            if line_count < _FILE_NODE_MIN_LINES:
                continue

            file_id = path_to_id("file", rel)
            file_ids_with_nodes.add(file_id)
            parent_mod = module_by_rel[rel]
            file_node = NodeFile(
                kind="file",
                id=file_id,
                name=filepath.stem,
                status="active",
                created=date,
                updated=date,
                path=rel,
                language=lang,
                refs=[Ref(rel="part_of", to=parent_mod)],
                extra={"loc": line_count},
            )
            count += _write(nodes_dir, file_node)

    # ---- Resolve inheritance refs across all discovered classes ----
    resolved = resolve_refs(all_class_defs)

    for cls_def, inheritance_refs in resolved:
        rel_filepath = _relpath(Path(cls_def.filepath), project_root)
        file_node_id = path_to_id("file", rel_filepath)

        if cls_def.kind == "interface":
            prefix = "iface"
        else:
            prefix = "cls"

        node_id = gen_id(prefix, cls_def.name)

        # Anchor the class to its file node when one exists, otherwise
        # to its module node; never reference a node that was not created.
        refs: list[Ref] = []
        if (
            file_node_id in file_ids_with_nodes
            or (nodes_dir / "file" / f"{file_node_id}.yaml").is_file()
        ):
            refs.append(Ref(rel="part_of", to=file_node_id))
        else:
            parent_mod = module_by_rel.get(rel_filepath, "")
            if parent_mod and (
                nodes_dir / "module" / f"{parent_mod}.yaml"
            ).is_file():
                refs.append(Ref(rel="part_of", to=parent_mod))
        for rel_type, target_id in inheritance_refs:
            refs.append(Ref(rel=rel_type, to=target_id))

        cls_node = NodeFile(
            kind=cls_def.kind,
            id=node_id,
            name=cls_def.name,
            status="active",
            created=date,
            updated=date,
            path=rel_filepath,
            line=cls_def.line,
            language=cls_def.language,
            refs=refs,
        )
        count += _write(nodes_dir, cls_node)

    # ---- Test file nodes ----
    if is_project_root:
        t_roots = [str(project_root / d) for d in test_dirs(str(project_root))]
    else:
        t_roots = workspace_test_dirs(ws_root)

    tp = test_pattern(lang)

    for t_root in t_roots:
        t_path = Path(t_root)
        if not t_path.is_dir():
            continue

        for testpath in _rglob_safe(t_path, tp):
            rel = _relpath(testpath, project_root)
            test_id = path_to_id("test", rel)

            # Derive a human-friendly test name from the filename.
            test_display = _test_display_name(testpath.stem, lang)

            test_node = NodeFile(
                kind="test",
                id=test_id,
                name=f"{test_display} Tests",
                status="active",
                created=date,
                updated=date,
                path=rel,
                refs=[],
                extra={
                    "test_type": "unit",
                    "framework": test_fw,
                },
            )
            count += _write(nodes_dir, test_node)

    return count


# ---------------------------------------------------------------------------
# Config nodes
# ---------------------------------------------------------------------------


def _create_config_nodes(
    project_root: Path,
    nodes_dir: Path,
    date: str,
) -> int:
    """Create config nodes for well-known config files at the project root.

    Returns the number of new nodes written.
    """
    count = 0

    for filename, config_type in _CONFIG_FILES:
        filepath = project_root / filename
        if not filepath.is_file():
            continue

        # Sanitise: replace non-alphanumeric with hyphens, strip leading hyphen.
        sanitised = re.sub(r"[^a-z0-9]", "-", filename.lower()).strip("-")
        cfg_id = f"cfg-{sanitised}"

        cfg_node = NodeFile(
            kind="config",
            id=cfg_id,
            name=filename,
            status="active",
            created=date,
            updated=date,
            path=filename,
            refs=[],
            extra={"config_type": config_type},
        )
        count += _write(nodes_dir, cfg_node)

    return count


# ---------------------------------------------------------------------------
# Node helpers
# ---------------------------------------------------------------------------


def _tech_node(name: str, category: str, date: str) -> NodeFile:
    """Build a technology NodeFile."""
    return NodeFile(
        kind="technology",
        id=f"tech-{name}",
        name=name,
        status="active",
        created=date,
        updated=date,
        refs=[],
        extra={"category": category},
    )


def _write(nodes_dir: Path, node: NodeFile) -> int:
    """Write a node if it does not already exist.  Returns 1 if written, 0 otherwise."""
    try:
        return 1 if write_node_if_new(nodes_dir, node) else 0
    except (OSError, ValueError) as exc:
        _warn(f"  Warning: could not write {node.id}: {exc}")
        return 0


# ---------------------------------------------------------------------------
# File utilities
# ---------------------------------------------------------------------------


def _rglob_safe(directory: Path, pattern: str) -> list[Path]:
    """Recursively glob for files, excluding common non-project directories.

    Returns a sorted list of matching paths.  Silently skips entries that
    raise permission or encoding errors.
    """
    results: list[Path] = []

    try:
        for p in directory.rglob(pattern):
            # Skip directories (rglob can match dirs if the pattern is loose).
            if not p.is_file():
                continue

            # Check that no excluded directory appears in the path parts.
            parts = p.relative_to(directory).parts
            if _EXCLUDE_DIRS.intersection(parts):
                continue

            results.append(p)
    except (OSError, ValueError):
        # Permission error or broken symlink - skip silently.
        pass

    results.sort()
    return results


def _count_lines(filepath: Path) -> int:
    """Count lines in a file.  Returns 0 on any read error."""
    try:
        return sum(1 for _ in filepath.open(encoding="utf-8", errors="replace"))
    except OSError:
        return 0


def _relpath(filepath: Path, root: Path) -> str:
    """Return a POSIX-style relative path from *root* to *filepath*.

    Falls back to the filename alone if the path cannot be made relative.
    Uses forward slashes regardless of platform.
    """
    try:
        return str(filepath.relative_to(root)).replace(os.sep, "/")
    except ValueError:
        return filepath.name


def _scan_safe(filepath: Path, lang: str) -> list[ClassDef]:
    """Run the scanner on a single file, catching all errors."""
    try:
        return scan_file(str(filepath), lang)
    except Exception:
        # Encoding issues, permission denied, corrupt files - skip.
        return []


def _test_display_name(stem: str, lang: str) -> str:
    """Derive a human-friendly name from a test file stem.

    Strips common test prefixes/suffixes:
      - ``test_auth``    -> ``auth``
      - ``auth.test``    -> ``auth``
      - ``auth_test``    -> ``auth``
      - ``AuthTest``     -> ``AuthTest``  (left as-is for Java/Kotlin)
    """
    # Python style: test_foo
    if stem.startswith("test_"):
        return stem[5:]
    # JS/TS style: foo.test (already stripped by Path.stem for .test.ts)
    if stem.endswith(".test"):
        return stem[:-5]
    # Go style: foo_test
    if stem.endswith("_test"):
        return stem[:-5]
    return stem


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _info(msg: str) -> None:
    """Print an informational message to stdout."""
    print(msg, flush=True)


def _warn(msg: str) -> None:
    """Print a warning message to stderr."""
    print(msg, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point: ``python -m akemi.bootstrap [project_root] [depth]``."""
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    depth = sys.argv[2] if len(sys.argv) > 2 else "tier2"

    if depth not in ("tier1", "tier2"):
        _warn(f"Invalid depth '{depth}'. Must be 'tier1' or 'tier2'.")
        sys.exit(1)

    run_bootstrap(project_root=project_root, depth=depth)


if __name__ == "__main__":
    main()
