# Akemi Graph Maintenance

## Three-Tier Reading Pattern

AI agent read codebase in tiers:

1. **Tier 0 - Views** (~50 tokens each): Read `views/architecture.md` first.
   Domain/module map in ~20 lines. Start here.

2. **Tier 1 - Index** (~500-2000 tokens): Read `index.yaml` for node
   inventory + edge adjacency list. Short keys save tokens.

3. **Tier 1.5 - Journeys** (variable): Read `.akemi/journeys/journey-*.yaml`
   for relevant user workflow. Maps UI states, transitions, API calls,
   backend processes as state machine. Read before coding user-facing feature.

4. **Tier 2 - Node files** (~50-100 tokens each): Read individual nodes only
   when need markdown body (rationale, description, contract).

NEVER read all node files. Use index to find what need.

## When to Update the Graph

| Event | Action |
|-------|--------|
| New file created | Create file node |
| New class created | Create class + interface nodes |
| New API endpoint | Create API node |
| New database table | Create resource node |
| File modified | Update node (loc, refs, updated date) |
| File deleted | Set node status to `deprecated` |
| File moved/renamed | Update node path, keep same ID |
| New dependency added | Add `depends_on` ref |
| Architecture decision | Create ADR node |

## After Any Graph Change

1. Run `bash .akemi/scripts/rebuild-index.sh`
2. Run `bash .akemi/scripts/rebuild-views.sh`
3. Run `bash .akemi/scripts/validate.sh` to check integrity

## Product Development Nodes

| Kind | Prefix | Use |
|------|--------|-----|
| epic | epic | Large initiatives spanning multiple stories |
| story | story | User stories with acceptance criteria |
| task | task | Atomic implementation units |
| bug | bug | Defects linked to affected code |

Hierarchy: `epic -> story -> task -> code + tests`

New edge types for product nodes:
- `breaks_into` - story breaks into tasks
- `affects` - bug affects code entity
- `fixed_by` - bug fixed by task

## User Journey State Machines

Journey files at `.akemi/journeys/journey-<name>.yaml`. Map
user workflows as state machines. See `.akemi/journeys/SCHEMA.md`
for full format.

| Event | Action |
|-------|--------|
| New user-facing feature | Create journey YAML before coding |
| Existing flow changed | Update journey states/transitions |
| New API added to flow | Add backend_process to transition |
| UI component rewired | Update trigger component/control_id |
| Flow no longer exists | Delete journey file |

Each journey gets `doc` graph node with `doc_type: journey` and
`documents` refs to files/APIs referenced.

Journey `graph_refs` validated by `validate.sh` (check #8).

## Design Documents

For complex epics, create design docs at `.akemi/designs/` before
implementation. Design docs capture full analysis, alternatives
considered, implementation plan. Complement ADR nodes which
record final decision.

## Node ID Rules

- Format: `<prefix>-<kebab-case-name>`
- Prefixes: dom, mod, file, cls, iface, fn, api, res, req, adr, tech, test, doc, cfg, epic, story, task, bug
- IDs permanent. Never reuse deprecated node's ID
- IDs globally unique across entire graph

## Edge Rules

- Store forward edges in node files (`refs` array)
- Inverse edges computed by `rebuild-index.sh`
- All `refs[].to` values must reference existing node IDs
- Use canonical edge types (see documentation-standards)
- `extends` = class-to-class or interface-to-interface inheritance
- `extends` NOT same as `depends_on` - use `extends` for inheritance, `depends_on` for composition/usage

## Transitive Edges

Index computes transitive closure for inheritance chains:
- If A `extends` B and B `extends` C, index infers A `extends` C
- If A `extends` B and B `implements` C, index infers A `implements` C

Inferred edges appear in index with `i: 1`, NOT stored in node files.
Only explicit edges belong in node files.

## Index Short Keys

Index uses short keys to save tokens:
- `k` = kind, `n` = name, `p` = path, `s` = status
- `r` = relationship, `t` = target
- Status omitted when `active` (default)