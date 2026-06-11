"""Graph operations for Akemi node relationships.

Replaces the transitive closure bash loop in rebuild-index.sh with
an in-memory adjacency map and iterative DFS.  Handles
extends/implements inheritance chains, cycles, and diamond
inheritance with proper deduplication.  Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass


def _reachable(adjacency: dict[str, list[str]], start: str) -> set[str]:
    """All nodes reachable from start by directed edges (iterative DFS).

    The start node itself is included only when it is reachable
    through a cycle, matching the closure semantics below.
    """
    seen: set[str] = set()
    stack = list(adjacency.get(start, ()))
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(adjacency.get(current, ()))
    return seen


@dataclass(frozen=True, slots=True)
class Edge:
    """A directed relationship between two Akemi nodes."""

    source: str   # node ID
    rel: str      # relationship type (extends, implements, depends_on, ...)
    target: str   # node ID
    inferred: bool = False

    @property
    def key(self) -> tuple[str, str, str]:
        """Deduplication key (ignores inferred flag)."""
        return (self.source, self.rel, self.target)


class AkemiGraph:
    """Directed graph for Akemi node relationships.

    Stores explicit edges added via :meth:`add_edge` and computes
    inferred edges via transitive closure over ``extends`` and
    ``implements`` chains.
    """

    def __init__(self) -> None:
        self._explicit: list[Edge] = []
        self._inferred: list[Edge] = []
        self._explicit_keys: set[tuple[str, str, str]] = set()
        self._closed: bool = False

    # ------------------------------------------------------------------
    # Building
    # ------------------------------------------------------------------

    def add_edge(self, source: str, rel: str, target: str) -> None:
        """Add an explicit (declared) edge."""
        edge = Edge(source=source, rel=rel, target=target, inferred=False)
        if edge.key in self._explicit_keys:
            return  # already present
        self._explicit_keys.add(edge.key)
        self._explicit.append(edge)
        # Invalidate any previous closure.
        self._closed = False

    # ------------------------------------------------------------------
    # Transitive closure
    # ------------------------------------------------------------------

    def compute_transitive_closure(self) -> list[Edge]:
        """Compute transitive closure for extends/implements chains.

        Rules:
          - If A extends B and B extends C  -> infer A extends C
          - If A extends B and B implements C -> infer A implements C

        Algorithm:
          1. Build a *subgraph* containing only ``extends`` edges.
          2. For each node A in the extends subgraph, find all
             descendants reachable via ``extends`` chains.
          3. For each descendant C:
             a. If A does not already have an ``extends`` edge to C,
                add an inferred ``extends`` edge.
             b. For every ``implements`` edge leaving C, if A does not
                already have that ``implements`` edge, add an inferred
                ``implements`` edge.
          4. Dedup by (source, rel, target).

        Handles:
          - Cycles in extends chains (skips self-edges).
          - Diamond inheritance (dedup via set).
          - Arbitrary depth of nesting.

        Returns the complete list of edges (explicit + inferred).
        """
        self._inferred.clear()

        # 1. Build extends-only adjacency map.
        extends_adj: dict[str, list[str]] = {}
        for edge in self._explicit:
            if edge.rel == "extends":
                extends_adj.setdefault(edge.source, []).append(edge.target)

        # Pre-index implements edges by source for O(1) lookup.
        implements_by_source: dict[str, set[str]] = {}
        for edge in self._explicit:
            if edge.rel == "implements":
                implements_by_source.setdefault(edge.source, set()).add(edge.target)

        # Collect all existing keys (explicit) for fast membership test.
        all_keys: set[tuple[str, str, str]] = set(self._explicit_keys)
        new_inferred: list[Edge] = []

        # 2. For each node with outgoing extends edges, find all
        #    transitively reachable ancestors.
        for node in extends_adj:
            descendants = _reachable(extends_adj, node)

            for desc in descendants:
                # Skip self-edges (cycles).
                if desc == node:
                    continue

                # 3a. Infer extends edge.
                key_ext = (node, "extends", desc)
                if key_ext not in all_keys:
                    all_keys.add(key_ext)
                    new_inferred.append(
                        Edge(source=node, rel="extends", target=desc, inferred=True)
                    )

                # 3b. Infer implements edges from the descendant.
                for impl_target in implements_by_source.get(desc, set()):
                    if impl_target == node:
                        continue  # skip self
                    key_impl = (node, "implements", impl_target)
                    if key_impl not in all_keys:
                        all_keys.add(key_impl)
                        new_inferred.append(
                            Edge(
                                source=node,
                                rel="implements",
                                target=impl_target,
                                inferred=True,
                            )
                        )

        self._inferred = new_inferred
        self._closed = True
        return self._explicit + self._inferred

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def all_edges(self) -> list[Edge]:
        """Return all edges including inferred ones after closure.

        If :meth:`compute_transitive_closure` has not been called yet,
        returns only explicit edges.
        """
        return self._explicit + self._inferred

    def edges_for(self, source: str) -> list[Edge]:
        """Return all edges originating from *source* (explicit + inferred)."""
        return [e for e in self.all_edges() if e.source == source]

    @property
    def explicit_edges(self) -> list[Edge]:
        """Return only explicitly added edges."""
        return list(self._explicit)

    @property
    def inferred_edges(self) -> list[Edge]:
        """Return only inferred edges (from transitive closure)."""
        return list(self._inferred)

    @property
    def node_ids(self) -> set[str]:
        """Return the set of all node IDs that appear in any edge."""
        ids: set[str] = set()
        for e in self.all_edges():
            ids.add(e.source)
            ids.add(e.target)
        return ids

    def __len__(self) -> int:
        """Total number of edges (explicit + inferred)."""
        return len(self._explicit) + len(self._inferred)
