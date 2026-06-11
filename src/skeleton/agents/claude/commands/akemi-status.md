---
description: "Show Akemi graph health metrics and status"
---

Read `.akemi/graph/index.yaml` and report a compact dashboard:

1. **Node counts** by kind (table), total nodes, total edges
2. **Staleness**: does `.akemi/.index-stale` exist? If yes, run `bash .akemi/scripts/rebuild-index.sh`, then report
3. **Last rebuild**: `generated` timestamp from the index
4. **Health** (from index data, no full node scan):
   - class/function nodes without incoming `tests` edges
   - api- nodes missing auth or test refs
   - nodes with `status` other than `active` (deprecated count)
5. **Backlog snapshot**: work item counts by status from `views/backlog.md` if present (epics, capabilities, features, stories, tasks, bugs)
6. **Standards**: coverage threshold and file limits configured in `.akemi/akemi.yaml`

End with a recommendation: clean, or which command/agent to run next
(`/akemi-validate` for integrity issues, Akemi-Tester for coverage gaps,
`/akemi-update` if source files lack nodes).

If `index.yaml` is missing, the graph is not initialized: suggest `bash .akemi/scripts/bootstrap.sh`.
