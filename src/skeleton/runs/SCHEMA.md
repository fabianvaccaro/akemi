# Run Ledger YAML Schema

> Canonical schema for Akemi orchestration run files.
> All run YAML files MUST conform to this schema.

A run is the persistent record of one orchestrated piece of work: the goal,
the steps delegated to agents, what each agent handed back, and whether an
independent agent verified the result. The run file is the only channel
agents can rely on to communicate with each other. Conversation context is
lost between agent invocations; the run file is not.

## File Location

All runs live at `.akemi/runs/run-<slug>.yaml`. Template:
`.akemi/templates/run-template.yaml`.

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `akemi` | string | yes | Schema version, currently `v1` |
| `kind` | string | yes | Always `run` |
| `id` | string | yes | `run-<kebab-case-slug>`, matches the filename |
| `name` | string | yes | The goal in one line |
| `status` | string | yes | `open`, `in_progress`, `blocked`, `done`, `abandoned` |
| `created` | date | yes | YYYY-MM-DD |
| `updated` | date | yes | YYYY-MM-DD, set on every write |
| `graph_refs` | list | no | Work item node IDs this run executes (story-, task-, bug-) |
| `steps` | list | yes | Ordered list of step definitions |
| `messages` | list | no | Free-form agent-to-agent notes |

## Step Definition

```yaml
steps:
  - id: st01-implement-service     # Unique within this run
    agent: Akemi-Developer          # Agent responsible for the step
    action: "Implement cls-user-service per iface-user-service"
    inputs: [task-add-user, iface-user-service]  # Node IDs to read first
    depends_on: [st00-design]       # Step IDs that must be done first
    status: pending                 # See step statuses below
    handoff:                        # Written by the executing agent
      nodes: [cls-user-service]     # Node IDs created or updated
      summary: "One line of what changed and why"
      validation: "0 errors"        # Last validate.sh result
      blockers: []                  # What stops the step, if anything
    verification:                   # Written by Akemi-Auditor only
      verdict: pass                 # pass | fail
      checks: ["nodes exist", "tests pass", "criteria met"]
      notes: ""
```

### Step Statuses

- **pending**: not started, or waiting on `depends_on`
- **in_progress**: an agent is working on it
- **done**: the executing agent finished and wrote its handoff
- **failed**: the agent could not complete it; `handoff.blockers` says why
- **blocked**: waiting on something outside the run (user decision, external system)
- **verified**: Akemi-Auditor confirmed the handoff; only the auditor sets this

A step is complete at `verified`, not at `done`. The agent that executed a
step never verifies its own work.

## Message Definition

Messages carry context that does not fit a handoff: questions, warnings,
constraints discovered mid-step.

```yaml
messages:
  - from: Akemi-Developer
    to: Akemi-Tester
    re: st01-implement-service     # Step ID the message is about
    body: "Token expiry is configurable; test both bounds."
```

## Validation Rules

Enforced by `validate.sh` (check #10):

1. All `graph_refs`, step `inputs`, and `handoff.nodes` MUST exist in
   `.akemi/graph/index.yaml`
2. All `depends_on` entries MUST reference step IDs in the same run
3. `status` values MUST come from the lists above (warning)
4. A step with `status: verified` MUST have a `verification` block (warning)
5. A run with `status: done` SHOULD have every step done or verified (warning)

## Lifecycle Rules

1. One run per orchestrated task. Re-running a task resumes its run file
   instead of starting a new one.
2. Agents write only their own step's `handoff` and append `messages`;
   the orchestrator owns `status` transitions and step definitions;
   Akemi-Auditor owns `verification` blocks.
3. Run files are kept after completion as the audit trail. Never delete a
   run file; set `status: abandoned` for work that will not continue.
4. Every write sets `updated`.
