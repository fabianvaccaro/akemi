---
description: "Summarize the SAFe backlog: work items, states, and what to pull next"
---

Summarize the project backlog.

1. Read `.akemi/graph/views/backlog.md`. If missing, run `bash .akemi/scripts/rebuild-views.sh` and retry; still missing means no work item nodes exist yet: suggest `/akemi-plan`.
2. If `.akemi/.index-stale` exists, run `bash .akemi/scripts/rebuild-index.sh` first.
3. For detail beyond the view (acceptance criteria, WSJF fields), read the specific node YAML under `.akemi/graph/nodes/{epic,capability,feature,story,task,bug}/`.

Report:

- **Hierarchy**: epic -> capability -> feature -> story tree (children `realizes` parents), each with status
- **Current PI/iteration**: pi- and iter- nodes, stories `planned_for` the active iteration, objective (obj-) progress
- **By status**: counts of planned / in_progress / completed / blocked items; list blocked tasks with blockers
- **Bugs**: open bugs with their `affects` targets and fix tasks
- **Next up**: top planned stories by WSJF (business_value + time_criticality + risk_reduction) / job_size, with unmet `depends_on` flagged

If $ARGUMENTS names a node ID (e.g. `feat-sso`), scope the report to that subtree.

Do not edit the backlog view by hand: change work item node YAML
(via Akemi-Planner or `/akemi-plan`), then `bash .akemi/scripts/rebuild-views.sh`.
