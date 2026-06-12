---
name: akemi-propose
description: "Design proposal workflow with self-verification: research the graph, draft, review, verify, persist. Usage: /akemi-propose <topic>"
tools: Read, Write, Edit, Glob, Grep, Bash
user-invocable: true
---

Produce a design proposal for a new feature, schema, or component. The proposal is researched in the graph, reviewed from the architecture and testing perspectives, and self-verified before it is presented. Run all stages in order; never skip one. Each stage writes into the proposal document.

## Setup

1. Parse $ARGUMENTS for the topic; build the slug `<kebab-case-topic>`. Topic too vague to research: ask the user for the driving requirement first.
2. If `.akemi/.index-stale` exists: `bash .akemi/scripts/rebuild-index.sh`. If `index.yaml` is missing entirely, suggest `bash .akemi/scripts/bootstrap.sh` and stop.
3. The proposal document is `.akemi/docs/proposals/<slug>.md`. Create the directory if needed. If the file already exists, read it and resume from the last completed stage instead of starting over.

## Stage 1: Research the graph

1. Read `.akemi/graph/views/architecture.md` and `views/backlog.md`.
2. Search `.akemi/graph/index.yaml` for nodes related to the topic: adr-, req-, doc-, feat-, dom-, mod-.
3. Read the node YAML of every relevant hit. Collect the constraints from adr- nodes verbatim; they bind every later stage.
4. Write the "Research" section: what the graph already knows, the binding ADR constraints (by node ID), and the gaps. Every claim cites a node ID.

## Stage 2: Draft

Write the "Design" section:

- Problem and goal, stated in terms of the requirement or work item driving it.
- The design itself: schemas, interfaces, module boundaries, data flow. Concrete, no placeholders.
- Rationale per decision, citing the ADR or requirement node it satisfies.
- Alternatives considered and why rejected.
- Impact: which existing nodes (modules, classes, APIs) change. Find them by following `depends_on` edges in the index from every touched node.
- New dependencies or technologies, each with its license. Flag anything that is not permissive (MIT, BSD, Apache-2.0, ISC).
- Open questions only the user can answer.

## Stage 3: Architecture review

Re-read the draft as Akemi-Architect would:

1. Check the design against every adr- constraint from Stage 1. On conflict: change the design, or draft a superseding adr- node with `status: proposed`. Never ignore a constraint silently.
2. Check module boundaries against `views/architecture.md` and dependency direction against `views/dependency-tree.md`. The design must not introduce cycles.
3. If the design sets a new lasting decision, draft the adr- node for it now from `.akemi/templates/node/adr.yaml`.

Append the "Architecture review" section: checks done, conflicts found, resolutions applied.

## Stage 4: Test plan

Derive the test plan from business value and architecture, never from a file list.

1. Write acceptance criteria for the proposal: observable behaviors, each one testable.
2. For each criterion, plan the cheapest test that would catch its failure, per `.akemi/guidelines/testing-standards.md`: unit for pure logic and business rules, integration where the design crosses a module or external boundary, e2e only for the critical user flow.
3. Order by risk: business value of the parent work item (WSJF when present) times the blast radius of failure (how many nodes depend on the touched node in the index).
4. Every planned test names the behavior, the criterion it protects, and the boundary it exercises. Reject filler: no tests for getters, framework behavior, configuration, or coverage numbers with no failing behavior behind them.

Append the "Test plan" section as a table: behavior | criterion | level | risk.

## Stage 5: Persist to the graph

1. Create `doc-proposal-<slug>` from `.akemi/templates/node/doc.yaml`: `path: .akemi/docs/proposals/<slug>.md`, `doc_type: proposal`, refs to the nodes the proposal touches.
2. Write any drafted adr- nodes with `status: proposed`.
3. Rebuild and check:
   ```bash
   bash .akemi/scripts/rebuild-index.sh
   bash .akemi/scripts/rebuild-views.sh
   bash .akemi/scripts/validate.sh
   ```
   FAIL lines: fix the named node YAML, re-run, max 3 attempts, then report the FAIL output verbatim and stop.

## Stage 6: Self-verification gate

Verify the proposal before presenting it. Run every check and record each result in a "Verification" section of the document.

| Check | How |
|---|---|
| Cited IDs exist | grep every node ID mentioned in the document against `index.yaml` |
| ADR compliance | every Stage 1 constraint is satisfied or superseded by a drafted adr- node |
| Criteria covered | every acceptance criterion has at least one planned test |
| No orphan tests | every planned test maps back to a criterion |
| Impact complete | every node whose `depends_on` points at a touched node appears in the Impact section |
| Licenses | every new dependency lists a license and none is copyleft |
| Graph clean | Stage 5 validate ended with 0 errors |

Any check fails: revise the affected stage and re-verify. Max 3 cycles, then list the still-failing checks honestly under "Open issues". Never present a proposal that hides a failed check.

## Stage 7: Report

Mark the document header `status: proposed (awaiting approval)`. Report: the proposal path, the decisions the user must make, the verification result, and one line of graph changes (nodes created/updated, validation result). After approval, hand off to /akemi-plan to decompose the proposal into work items.

## Failure handling

- A template or script is missing: report the exact path or command and its error; do not invent schemas or improvise checks.
- Research finds nothing related in the graph: say so in the Research section and proceed; do not fabricate citations.
