---
name: akemi-explore
description: "Navigate the Akemi graph to understand the codebase. Auto-invoked when understanding project architecture, finding related code, or tracing dependencies."
tools: Read, Glob, Grep, Bash
user-invocable: false
---

Read the graph in tiers, cheapest first. Never read all node files.

## Steps

1. If `.akemi/.index-stale` exists: `bash .akemi/scripts/rebuild-index.sh` before trusting the index.

2. Overview: read `.akemi/graph/views/architecture.md` (domain/module map, ~30 lines).
   Other views by question:
   - Work items / backlog state: `views/backlog.md`
   - Test coverage gaps: `views/test-coverage.md`
   - Endpoints: `views/api-surface.md`
   - Stack and versions: `views/tech-stack.md`
   - Coupling and cycles: `views/dependency-tree.md`

3. Find a specific node: search `.akemi/graph/index.yaml` by name or path. The index uses short keys: `k`=kind, `n`=name, `p`=path, `s`=status, `r`=rel, `t`=target.

4. Trace dependencies: follow the `edges` adjacency list in the index from the start node. Inferred edges are marked `i: 1`.

5. Detail (rationale, contracts, acceptance criteria): read `.akemi/graph/nodes/<kind>/<id>.yaml` for the specific nodes only.

6. User-facing flows: read the relevant `.akemi/journeys/journey-*.yaml` (UI states, transitions, API calls, backend processes).

## Failure Handling

- `index.yaml` missing: the graph is not initialized; suggest `bash .akemi/scripts/bootstrap.sh` and stop.
- A node referenced in the index has no file, or a view is missing: report it and suggest `/akemi-validate`; do not reconstruct generated files by hand.
- Entity not in the graph at all: fall back to targeted Glob/Grep of the source, then note the missing node so it gets created.
