---
description: "Run a PI or iteration planning session, creating SAFe work item nodes"
---

Guide a planning session and persist the result as graph nodes. Act as Akemi-Planner.
Rules: `.akemi/guidelines/safe-scrum.md`. Templates: `.akemi/templates/node/`.

## Session

1. **Context**: read `views/backlog.md` and `views/architecture.md`. If `.akemi/.index-stale` exists, run `bash .akemi/scripts/rebuild-index.sh`. Ask what is being planned: a new initiative, a PI, or an iteration.

2. **Decompose** (new initiative): work top-down with the user:
   - epic- (large initiative) -> cap- (capability) -> feat- (feature) -> story- (user story with acceptance criteria in the body) -> task- (atomic units, each with a test task)
   - Each child gets `{ rel: realizes, to: <parent-id> }`; tasks get `{ rel: part_of, to: <story-id> }`
   - Bugs raised during planning: bug- nodes with `{ rel: affects, to: <code-node-id> }`

3. **Prioritize**: for each epic/capability/feature set WSJF fields: `business_value`, `time_criticality`, `risk_reduction`, `job_size` (1-10 each). Rank by (bv + tc + rr) / job_size.

4. **Schedule** (PI/iteration planning):
   - Create the pi- node and its iter- nodes with `{ rel: part_of, to: <pi-id> }`
   - Create obj- nodes for PI objectives with `{ rel: supported_by, to: <feat-/story-id> }`
   - Assign stories: `{ rel: planned_for, to: <iter-id> }`, ordered by WSJF and `depends_on` topology; do not overcommit past the user's stated capacity

5. **Persist**: write each node to `.akemi/graph/nodes/<kind>/<id>.yaml` (under 120 lines, ID = filename), then:
   ```bash
   bash .akemi/scripts/rebuild-index.sh
   bash .akemi/scripts/rebuild-views.sh
   bash .akemi/scripts/validate.sh
   ```
   FAIL lines: fix the named nodes, re-run, max 3 attempts, then report the FAIL output verbatim.

6. **Output**: the plan as a tree with node IDs, WSJF ranking, iteration assignments, and one line: nodes created, validation result.
