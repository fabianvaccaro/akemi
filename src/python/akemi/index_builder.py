"""Build the compact .akemi/graph/index.yaml from node files.

Replaces rebuild-index.sh with pure Python.  Reads all node YAML files,
counts them by kind, builds a transitive closure of extends/implements
chains, and writes a compact index using short keys for token efficiency.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .graph import AkemiGraph, Edge
from .node import NodeFile, read_all_nodes
from .paths import now_iso

ALL_KINDS: list[str] = [
    "domain",
    "module",
    "file",
    "class",
    "interface",
    "function",
    "api",
    "resource",
    "requirement",
    "adr",
    "technology",
    "test",
    "doc",
    "config",
    "epic",
    "story",
    "task",
    "bug",
    "capability",
    "feature",
    "pi",
    "iteration",
    "objective",
]


def build_index(akemi_dir: str | Path) -> str:
    """Build and write ``.akemi/graph/index.yaml``.

    Steps:
      1. Read all node files from ``nodes_dir``.
      2. Count by kind.
      3. Build compact nodes section using short keys.
      4. Collect all explicit edges into :class:`AkemiGraph`.
      5. Run transitive closure.
      6. Build edges section with short keys.
      7. Write ``index.yaml``.
      8. Remove ``.index-stale`` flag if present.

    Returns a summary string like
    ``"Index rebuilt: 449 nodes (2026-04-01T12:00:00Z)"``
    """
    akemi_dir = Path(akemi_dir)
    nodes_dir = akemi_dir / "graph" / "nodes"
    index_file = akemi_dir / "graph" / "index.yaml"

    if not nodes_dir.is_dir():
        raise FileNotFoundError(
            f"{nodes_dir} not found. Run install first."
        )

    # 1. Read all nodes.
    nodes = read_all_nodes(nodes_dir)
    total = len(nodes)
    timestamp = now_iso()

    # 2. Count by kind.
    kind_counts: Counter[str] = Counter()
    for node in nodes.values():
        kind_counts[node.kind] += 1

    # 3. Build compact nodes section.
    #    Format: {id}: { k: kind, n: "name", p: "path", s: status }
    #    Omit s when status is 'active' (default).
    #    Omit p when empty.
    nodes_lines: list[str] = []
    for nid in sorted(nodes.keys()):
        node = nodes[nid]
        parts = [f'k: {node.kind}', f'n: "{node.name}"']
        if node.path:
            parts.append(f'p: "{node.path}"')
        if node.status and node.status != "active":
            parts.append(f"s: {node.status}")
        entry = ", ".join(parts)
        nodes_lines.append(f"  {nid}: {{ {entry} }}")

    # 4. Collect all explicit edges into graph.
    graph = AkemiGraph()
    for nid, node in nodes.items():
        for ref in node.refs:
            if ref.rel and ref.to:
                graph.add_edge(nid, ref.rel, ref.to)

    # 5. Run transitive closure.
    all_edges = graph.compute_transitive_closure()

    # 6. Build edges section.
    #    Group by source, then list: { r: rel, t: target } with i: 1 for inferred.
    edges_by_source: dict[str, list[Edge]] = {}
    for edge in all_edges:
        edges_by_source.setdefault(edge.source, []).append(edge)

    edges_lines: list[str] = []
    for source in sorted(edges_by_source.keys()):
        edges_lines.append(f"  {source}:")
        # Sort edges within a source for deterministic output.
        source_edges = sorted(
            edges_by_source[source], key=lambda e: (e.rel, e.target)
        )
        for edge in source_edges:
            if edge.inferred:
                edges_lines.append(
                    f"    - {{ r: {edge.rel}, t: {edge.target}, i: 1 }}"
                )
            else:
                edges_lines.append(
                    f"    - {{ r: {edge.rel}, t: {edge.target} }}"
                )

    # 7. Write index.yaml using string formatting for compact output.
    by_kind_lines: list[str] = []
    for kind in ALL_KINDS:
        by_kind_lines.append(f"    {kind}: {kind_counts.get(kind, 0)}")

    nodes_block = "\n".join(nodes_lines) if nodes_lines else "  {}"
    edges_block = "\n".join(edges_lines) if edges_lines else "  {}"

    content = (
        "---\n"
        "akemi: v1\n"
        "kind: index\n"
        f"generated: {timestamp}\n"
        "stats:\n"
        f"  total_nodes: {total}\n"
        "  by_kind:\n"
        + "\n".join(by_kind_lines)
        + "\n"
        "\n"
        "nodes:\n"
        + nodes_block
        + "\n"
        "\n"
        "edges:\n"
        + edges_block
        + "\n"
    )

    index_file.parent.mkdir(parents=True, exist_ok=True)
    index_file.write_text(content, encoding="utf-8")

    # 8. Remove stale flag.
    stale_flag = akemi_dir / ".index-stale"
    if stale_flag.exists():
        stale_flag.unlink()

    return f"Index rebuilt: {total} nodes ({timestamp})"
