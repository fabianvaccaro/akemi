---
globs: .akemi/runs/**/*.yaml
---
# Akemi Run Ledger Rules

When editing files under `.akemi/runs/` (schema: `.akemi/runs/SCHEMA.md`):

1. `id` equals the filename without `.yaml` and starts with `run-`
2. Write only what your role owns: executing agents write their own step's
   `handoff` and append `messages`; the orchestrator owns run `status` and step
   definitions; Akemi-Auditor owns `verification` blocks
3. A step is complete at `status: verified`, never at `done`. The agent that
   executed a step never verifies it
4. Every `graph_refs`, `inputs`, and `handoff.nodes` entry is an existing node ID
   in `.akemi/graph/index.yaml`
5. Statuses are canonical. Run: open, in_progress, blocked, done, abandoned.
   Step: pending, in_progress, done, failed, blocked, verified
6. Set `updated` to today's date on every write
7. Never delete a run file; set `status: abandoned` for work that will not continue
8. After editing run files, `bash .akemi/scripts/validate.sh` checks them (check #10)
