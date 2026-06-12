# Akemi Development System

This project is governed by Akemi: a text-YAML graph in `.akemi/graph/` that documents
the codebase. All work is graph-first: query before work, update after work.

## Graph-First Workflow

Before any work:
1. Read `.akemi/graph/views/architecture.md` (project map, ~30 lines)
2. Look up node IDs, paths, and edges in `.akemi/graph/index.yaml`. Use the index instead of grepping the codebase for structure it already maps
3. Read node YAML (`.akemi/graph/nodes/<kind>/<id>.yaml`) only when you need the body (rationale, contract)
4. For work items read `.akemi/graph/views/backlog.md`; for user flows read `.akemi/journeys/`

If `.akemi/.index-stale` exists, run `bash .akemi/scripts/rebuild-index.sh` before trusting the index.

After any code change (file created, modified, moved, deleted):
1. Create/update the matching node YAML in `.akemi/graph/nodes/`
2. `bash .akemi/scripts/rebuild-index.sh`
3. `bash .akemi/scripts/rebuild-views.sh`
4. `bash .akemi/scripts/validate.sh`

Never edit `index.yaml` or `views/*.md` by hand: they are generated. Edit node YAML, then rebuild.

## Scripts

| Script | Purpose |
|--------|---------|
| `bash .akemi/scripts/rebuild-index.sh` | Regenerate index.yaml from node files |
| `bash .akemi/scripts/rebuild-views.sh` | Regenerate views (architecture, backlog, api-surface, test-coverage, tech-stack, dependency-tree) |
| `bash .akemi/scripts/validate.sh` | Check graph integrity, prints PASS/FAIL/WARN lines |
| `bash .akemi/scripts/bootstrap.sh` | Initialize graph from existing code |
| `bash .akemi/scripts/sync-claude.sh` | Sync agent definitions into .claude/ |

## Node Kinds

| Kind | Prefix | Kind | Prefix | Kind | Prefix |
|------|--------|------|--------|------|--------|
| domain | dom- | api | api- | epic | epic- |
| module | mod- | resource | res- | capability | cap- |
| file | file- | requirement | req- | feature | feat- |
| class | cls- | adr | adr- | story | story- |
| interface | iface- | technology | tech- | task | task- |
| function | fn- | test | test- | bug | bug- |
| doc | doc- | config | cfg- | pi | pi- |
| | | | | iteration | iter- |
| | | | | objective | obj- |

IDs: `<prefix><kebab-case-name>`. File: `.akemi/graph/nodes/<kind>/<id>.yaml`, under 120 lines.
Relationships: `part_of`, `extends`, `implements`, `depends_on`, `tests`, `realizes`,
`planned_for`, `affects`, `supported_by`, `uses_technology`.

## SAFe Backlog Hierarchy

```
epic -> capability -> feature -> story -> task   (child `realizes` parent; task `part_of` story)
story planned_for iteration; iteration part_of pi; objective supported_by feature/story
bug affects code node; bug fixed via a task part_of a story
```

Never code without a task or story node. Details: `.akemi/guidelines/safe-scrum.md`.

## Agent Routing

| Work | Agent |
|------|-------|
| Multi-step or unclear tasks | Akemi-Orchestrator (decomposes, delegates) |
| Architecture, module boundaries, ADRs | Akemi-Architect |
| Backlog: epics, capabilities, features, stories, PI/iteration planning | Akemi-Planner |
| Writing or modifying code | Akemi-Developer |
| Code review | Akemi-Reviewer |
| Tests and coverage | Akemi-Tester |
| Graph nodes, docs, journeys | Akemi-Documenter |
| Splitting files, restructuring | Akemi-Refactorer |
| CI/CD, Docker, infrastructure | Akemi-DevOps |
| Security audits | Akemi-Security |
| Database schema, migrations | Akemi-DBA |
| API design, endpoint contracts | Akemi-API |

## Failure Protocol

- `validate.sh` fails: read the FAIL lines, fix the named node YAML files, re-run. Max 3 attempts, then report the remaining FAIL output verbatim and stop. Do not loop.
- A script is missing or errors: report the exact command and its stderr. Do not improvise an alternative.
- A referenced node ID does not exist: create the node or fix the ref. Never invent IDs.

## Monorepo Projects

If `.akemi/akemi.yaml` has `type: monorepo` with `workspaces:`, match the file path against
workspace `root:` values and apply that workspace's language and conventions (python, typescript,
java, scala, etc.), not the root defaults. Maven/Gradle/sbt modules count as workspaces.

## Standards

@.akemi/guidelines/coding-standards.md
@.akemi/guidelines/testing-standards.md
@.akemi/guidelines/graph-maintenance.md
@.akemi/guidelines/safe-scrum.md
@.akemi/guidelines/ai-friendly.md

## Commands

`/akemi-status` (graph health), `/akemi-graph` (topology), `/akemi-backlog` (work item summary),
`/akemi-plan` (PI/iteration planning), `/akemi-propose` (self-verified design proposal),
`/akemi-create-node`, `/akemi-scaffold`, `/akemi-validate`, `/akemi-update`.

End every task with one line summarizing graph changes: nodes created/updated and validation result.
