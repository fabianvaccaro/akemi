# MANDATORY: Akemi Development System

Project governed by Akemi. ALL dev work MUST follow Akemi workflow.
Skip rules → broken graph state + untested code.

## BEFORE doing ANY work

MUST read `.akemi/graph/views/architecture.md` first. Full project map <30 lines. NO coding/planning/reviewing without it.

Find specific code → read `.akemi/graph/index.yaml`, lookup nodes by name/path. NEVER grep whole codebase when graph maps it.

User-facing features → read journey file at `.akemi/journeys/` for current state machine (UI states, transitions, API calls, backend processes) before changes.

## Workspace Awareness (Monorepo Projects)

If `.akemi/akemi.yaml` has `type: monorepo` + `workspaces:` section → multi-stack project. Each workspace own language, framework, conventions.

Working on file:
1. Match file path against workspace `root:` values in `akemi.yaml`
2. Apply workspace language conventions (not root project defaults)
3. Use workspace test framework + patterns for test files
4. Reference workspace tech nodes (e.g., `tech-python` for Python workspace)

If `type: single` or no workspaces → ignore; all files share stack from `project.*` fields.

## MANDATORY: Use Akemi Agents

MUST use right Akemi agent every task. NO generic assistant. Route ALL work through specialists:

| Task | REQUIRED Agent |
|------|---------------|
| Any complex/multi-step task | **Akemi-Orchestrator** (decomposes and delegates) |
| System design, new modules, architecture | **Akemi-Architect** |
| Planning features, decomposing work | **Akemi-Planner** |
| Writing or modifying code | **Akemi-Developer** |
| Reviewing code changes | **Akemi-Reviewer** |
| Writing or checking tests | **Akemi-Tester** |
| Creating/updating graph nodes or docs | **Akemi-Documenter** |
| Restructuring, splitting files | **Akemi-Refactorer** |
| CI/CD, Docker, deployment | **Akemi-DevOps** |
| Security audits, vulnerability checks | **Akemi-Security** |
| Database schema, migrations, queries | **Akemi-DBA** |
| API design, endpoint contracts | **Akemi-API** |

Doubt → use **Akemi-Orchestrator**. Picks right agents.

## MANDATORY: Product Development Flow

ALL features MUST follow Akemi hierarchy:

```
epic -> story -> task -> code + tests
```

- **Epics** (`epic-`): Big initiatives. Made before implementation.
- **Stories** (`story-`): User stories + acceptance criteria. Belong to epic.
- **Tasks** (`task-`): Atomic implementation units. Belong to story. Link to code.
- **Bugs** (`bug-`): Defects linked to affected code + regression test tasks.

NEVER code without task node. Use **Akemi-Planner** to build hierarchy.

## MANDATORY: Standards

NON-NEGOTIABLE:

@.akemi/guidelines/coding-standards.md
@.akemi/guidelines/testing-standards.md
@.akemi/guidelines/graph-maintenance.md
@.akemi/guidelines/ai-friendly.md

## MANDATORY: After ANY Code Change

Create/modify/delete file → MUST:

1. Create/update graph node in `.akemi/graph/nodes/`
2. If change affects user flow → update journey file in `.akemi/journeys/`
3. Run `bash .akemi/scripts/rebuild-index.sh .akemi`
4. Run `bash .akemi/scripts/rebuild-views.sh .akemi`

Skip → graph stale, agents lose context.

## Available Commands

- `/akemi-status` - Show graph health metrics
- `/akemi-create-node` - Create a new graph node
- `/akemi-scaffold` - Scaffold new code from templates
- `/akemi-validate` - Check graph integrity
- `/akemi-update` - Update graph after code changes