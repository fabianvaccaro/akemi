---
description: "Start or resume an orchestrated run: decompose, delegate, verify every step"
---

Orchestrate a multi-step task through the run ledger. Act as Akemi-Orchestrator.
Schema: `.akemi/runs/SCHEMA.md`. Template: `.akemi/templates/run-template.yaml`.

1. **Heal first**: `bash .akemi/scripts/heal.sh && bash .akemi/scripts/validate.sh`.
   Start from a mechanically clean graph.

2. **Resolve the run**: if $ARGUMENTS names an existing run ID (`run-<slug>`), resume
   it from `.akemi/runs/<run-id>.yaml`. Otherwise treat $ARGUMENTS as the goal,
   confirm a story or task node covers it (route to Akemi-Planner if not), and create
   a new run file with steps: agent, action, input node IDs, `depends_on`.

3. **Execute**: delegate each unblocked step to its agent with the run ID and step ID.
   The agent reads its assignment from the run file and writes its handoff back.
   Read-only agents (Akemi-Reviewer, Akemi-Security) return findings; record their
   handoff for them.

4. **Verify**: after each `done` step, delegate verification to Akemi-Auditor. On
   `fail`, return the step to `pending` with the auditor's notes as a message to the
   owning agent; max 2 verification retries, then mark the step `failed`, the run
   `blocked`, and report.

5. **Close**: when all steps are `verified`, run
   ```bash
   bash .akemi/scripts/rebuild-index.sh
   bash .akemi/scripts/rebuild-views.sh
   bash .akemi/scripts/validate.sh
   ```
   update the work item statuses, and set the run `status: done`.

6. **Output**: run ID, the step table with statuses, and one line: steps
   verified/total, nodes created/updated, validation result.

The run file survives session loss; `/akemi-run run-<slug>` always resumes exactly
where the ledger says work stopped. Never mark a step `verified` for the agent that
executed it.
