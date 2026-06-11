---
name: akemi-explore
description: "Navigate the Akemi graph to understand the codebase. Auto-invoked when understanding project architecture, finding related code, or tracing dependencies."
tools: Read, Glob, Grep
user-invocable: false
---

Navigate Akemi graph via three-tier pattern:

1. ALWAYS start with `.akemi/graph/views/architecture.md`
   Domain/module map in ~20 lines.

2. Find specific node:
   Read `.akemi/graph/index.yaml`, search `nodes` map by name/path.

3. Node details:
   Read `.akemi/graph/nodes/<kind>/<id>.yaml`

4. User-facing feature → read journey:
   Read `.akemi/journeys/journey-*.yaml` for state machine mapping
   UI states, transitions, API calls, backend processes.

5. NEVER read all node files. Use index.

6. Trace dependency chain:
   Read `edges` section in index.yaml for start node,
   follow chain through adjacency list.

7. Test coverage:
   Read `.akemi/graph/views/test-coverage.md`

8. Full API surface:
   Read `.akemi/graph/views/api-surface.md`

9. Tech stack:
   Read `.akemi/graph/views/tech-stack.md`