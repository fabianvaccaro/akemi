# SAFe Scrum in the Akemi Graph

How Akemi maps SAFe work items onto graph nodes. Plain Scrum
projects can ignore capability/pi/objective and use
epic -> feature -> story directly.

## Work-Item Hierarchy

| Kind | Prefix | Scope |
|------|--------|-------|
| epic | epic | Portfolio initiative, months |
| capability | cap | Solution behavior, multiple features |
| feature | feat | User-visible value, fits one PI |
| story | story | Team-sized slice, fits one iteration |
| task | task | Atomic implementation unit |
| bug | bug | Defect |
| pi | pi | Program Increment (8-12 weeks) |
| iteration | iter | 2-week timebox inside a PI |
| objective | obj | PI Objective set at PI planning |

Hierarchy: `epic -> capability -> feature -> story -> task`.
Small setups may skip capability: feature realizes epic directly.

## Ref Rules

- capability: `realizes -> epic`
- feature: `realizes -> capability` (or epic directly)
- story: `realizes -> feature`, `planned_for -> iteration`,
  plus `implemented_by`/`tested_by` refs to code nodes
- task: `part_of -> story`
- bug: `affects -> story/feature/class`
- iteration: `part_of -> pi`
- objective: `part_of -> pi`, `supported_by -> feature(s)`

Validator check 9 warns (never fails) on stories without a
realizes ref to a feature/epic, features without a realizes ref
to a capability/epic, and iterations without part_of to a PI.
Skipped when graph has no feature/story/pi nodes.

## WSJF Prioritization

epic, capability, and feature nodes carry a `wsjf` block:

```yaml
wsjf:
  business_value: 8    # 1-10
  time_criticality: 5  # 1-10
  risk_reduction: 3    # 1-10
  job_size: 4          # 1-10
  score: 4.0           # (bv + tc + rr) / job_size
```

Compute `score` manually when the inputs change. Highest score
goes first. Backlog view shows scores next to features.

## States

- epic/capability: `funnel -> analyzing -> backlog -> implementing -> done`
- feature/story: `backlog -> refining -> ready -> in_progress -> done`
- task: `backlog -> in_progress -> done`

State lives in the node frontmatter `state` field. The `status`
field stays for graph lifecycle (planned/active/deprecated).

## PI and Iteration Cadence

- One `pi` node per Program Increment with `start`/`end` dates.
- 4-6 `iteration` nodes per PI, each with `number`, `start`,
  `end`, `capacity`, `committed_points`, and `part_of -> pi`.
- `objective` nodes record PI commitments with `business_value`
  and `committed: true|false` (false = stretch).
- At iteration planning, point stories at the iteration with
  `planned_for` and set `committed_points` on the iteration.

## Definition of Done

`acceptance_criteria` list on epic/capability/feature/story is
the definition of done. A work item is `done` only when every
criterion holds and linked tests pass. Keep criteria testable
and short.

## Agent Workflow

Creating a work item:
1. Copy the template from `.akemi/templates/node/<kind>.yaml`.
2. Place it at `.akemi/graph/nodes/<kind>/<id>.yaml`.
3. Add the refs listed above. Parent must exist first.
4. Run rebuild-index.sh, rebuild-views.sh, validate.sh.

Updating a work item:
- Move `state` forward as work progresses; set `updated`.
- When a story is done, check whether its feature is done.
- Never delete work items; set `status: deprecated`.

Read `views/backlog.md` for the current PI plan, backlog by
state, and epic-to-story traceability before planning work.
