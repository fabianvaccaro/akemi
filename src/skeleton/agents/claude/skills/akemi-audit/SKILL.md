---
name: akemi-audit
description: "Self-healing audit of the graph, plans, proposals, and runs. Heals mechanical issues, then verifies claims against reality. Usage: /akemi-audit [plans|proposals|runs|nodes|all]"
tools: Read, Edit, Glob, Grep, Bash
user-invocable: true
---

Audit the project the way Akemi-Auditor would: heal the mechanical layer first,
then check judgment-level claims against the graph and the source. Default scope
is `all`; $ARGUMENTS can narrow it to `plans`, `proposals`, `runs`, or `nodes`.

## Stage 1: Self-heal

1. Run:
   ```bash
   bash .akemi/scripts/heal.sh
   bash .akemi/scripts/validate.sh
   ```
2. Heal fixes ID mismatches, repoints moved files, and deprecates nodes for
   deleted files, then rebuilds the index. Record its FIXED lines for the report.
3. MANUAL lines from heal and FAIL lines from validate are findings. Fix what has
   one correct answer (per the /akemi-validate fix table); everything else goes in
   the report with its owning agent.
4. If either script itself errors (not FAIL lines), report the exact command and
   stderr and stop; do not improvise checks by hand.

## Stage 2: Audit plans

For every epic/capability/feature/story/task/bug node (use `views/backlog.md` and
the index, read node YAML for detail):

- Hierarchy: child `realizes` parent, task `part_of` story, story `planned_for`
  iteration where a PI exists
- Every story body has acceptance criteria; every implementation task has a test task
- WSJF fields present on epics, capabilities, features
- No `depends_on` cycles among tasks
- Status consistency: no completed story with pending tasks, no closed bug without
  a fix task and a regression test task

## Stage 3: Audit proposals

For every `.akemi/docs/proposals/*.md` not yet implemented, re-run the
/akemi-propose verification gate: cited node IDs exist in the index, ADR
constraints satisfied or superseded by a drafted adr- node, every acceptance
criterion has a planned test, every test maps to a criterion, the impact section
covers actual dependents from the index, every new dependency lists a permissive
license. A proposal that no longer passes gets each failed check named.

## Stage 4: Audit runs

For every `.akemi/runs/run-*.yaml` (schema: `.akemi/runs/SCHEMA.md`):

- Steps marked `done` for more than the run's lifecycle without verification:
  verify them now as Akemi-Auditor would (claims in the handoff against git diff,
  files, tests) and write the `verification` block
- Steps marked `verified` without a `verification` block: a finding
- Runs `done` with unfinished steps, or `in_progress` with nothing pending: a finding

## Stage 5: Audit nodes against reality

Sample-check the riskiest nodes (highest fan-in from the index, most recently
updated): refs match real imports, `path` points at the named entity, bodies say
WHY not WHAT, no `active` node for deleted code. Full mechanical coverage already
came from Stage 1; this stage is judgment.

## Stage 6: Report

Scorecard by area: healed (count), clean (count), findings as
`SEVERITY | target | claim | reality | owning agent`. Route fixes: code to
Akemi-Developer, nodes to Akemi-Documenter, plans to Akemi-Planner, tests to
Akemi-Tester, structure to Akemi-Architect. End with one line: areas audited,
issues healed, findings by severity, validation result.
