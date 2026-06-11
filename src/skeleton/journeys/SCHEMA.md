# Journey YAML Schema

> Canonical schema for Akemi user journey state machine files.
> All journey YAML files MUST conform to this schema.

## File Location

All journeys live at `.akemi/journeys/journey-<name>.yaml`.

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique journey ID: `journey-<kebab-case-name>` |
| `name` | string | yes | Human-readable journey name |
| `version` | integer | yes | Schema version (currently `1`) |
| `actor` | string | yes | Primary user role: `analyst`, `client`, `admin` |
| `description` | string | yes | What this journey covers |
| `states` | list | yes | Ordered list of state definitions |
| `transitions` | list | yes | List of transition definitions |
| `error_paths` | list | no | List of error transition definitions |
| `branching_conditions` | list | no | List of conditional routing rules |

## State Definition

Each state represents a discrete point in the user's workflow where they
can observe UI, make decisions, or wait for a system process.

```yaml
states:
  - id: s01-state-name           # Unique within this journey
    name: "Human-readable name"
    type: ui | system | background  # Who/what acts in this state
    page: path/to/component.tsx     # Exact file path (for ui states)
    graph_refs: [file-node-id]      # Akemi graph node IDs for this state
    description: "What the user sees or what the system does"
    reachable: true                 # false if blocked by unwired code
```

### State Types

- **ui**: User is interacting with a page/component. `page` is required.
- **system**: System processes a synchronous request (API call). `page` optional.
- **background**: System processes asynchronously (Celery, pipeline). No `page`.

## Transition Definition

Each transition connects two states via a trigger (user action or system event)
and optionally maps to a backend process.

```yaml
transitions:
  - id: t01-transition-name       # Unique within this journey
    from: s01-state-name          # Source state ID
    to: s02-state-name            # Target state ID
    trigger:
      type: user_action | system_event | auto
      ui_control: "Button label or control description"  # For user_action
      component: path/to/component.tsx                   # File containing the control
      control_id: "CONSTANT_NAME or line reference"      # How to find it in code
      graph_refs: [file-node-id]                         # Graph nodes for the trigger
    backend_process:               # Optional: what runs server-side
      api_endpoint: "METHOD /path" # e.g., "POST /upload"
      handler: path/to/handler.py  # Backend file
      graph_refs: [file-node-id]   # Graph nodes for the backend
    condition: "expression"        # Optional: when this transition is available
    notes: "Additional context"    # Optional
```

### Trigger Types

- **user_action**: User clicks/interacts with a UI control. `ui_control` required.
- **system_event**: System emits an event (webhook, status change, pipeline completion).
- **auto**: Automatic transition (redirect, polling result). No user interaction.

## Error Path Definition

Error paths document what happens when a transition fails.

```yaml
error_paths:
  - id: e01-error-name
    from: s03-state-name           # State where the error occurs
    to: s03-state-name             # Usually same state (retry) or error state
    trigger:
      type: system_event
      event: "validation_error"    # Error type
    description: "What happens and what the user sees"
    recovery: "How the user recovers" # Optional
```

## Branching Condition Definition

Branching conditions document conditional routing - where the next state
depends on application state rather than a user action.

```yaml
branching_conditions:
  - id: b01-condition-name
    at_state: s06-state-name       # State where branching occurs
    condition: "pyg_approved === false"  # JavaScript-like expression
    goto: s07-target-if-true
    else_goto: s13-target-if-false
    description: "Why this branching exists"
```

## Graph Node for Journeys

Each journey file gets a corresponding `doc` graph node:

```yaml
---
akemi: v1
id: doc-journey-<name>
kind: doc
name: "Journey: <Human Name>"
status: active
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
path: .akemi/journeys/journey-<name>.yaml
doc_type: journey
refs:
  - { rel: part_of, to: dom-<primary-domain> }
  - { rel: documents, to: file-<node-id> }  # For each file referenced
  - { rel: documents, to: api-<node-id> }   # For each API referenced
---
```

## Validation Rules

1. All `graph_refs` values MUST exist in `.akemi/graph/index.yaml`
2. All `from` and `to` in transitions MUST reference valid state IDs in the same journey
3. All `at_state`, `goto`, `else_goto` in branching_conditions MUST reference valid state IDs
4. Every state MUST be reachable via at least one transition (except the entry state s01)
5. States with `reachable: false` indicate known gaps that must be resolved before development
6. The `page` field on `ui` states MUST point to an existing file

## Mandatory Reading Order

Journey files are added to the Akemi reading protocol:

1. **Tier 0**: `views/architecture.md` (~50 tokens)
2. **Tier 1**: `index.yaml` (~500-2000 tokens)
3. **Tier 1.5**: `.akemi/journeys/` (relevant journey files)
4. **Tier 2**: Individual node files (on demand)
