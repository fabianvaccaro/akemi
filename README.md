# Akemi

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](src/python/pyproject.toml)
[![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#requirements)

Graph-based codebase documentation for AI coding agents. Akemi keeps the structure of your project as a knowledge graph of plain YAML nodes and relations inside the repository, with no database and no server. AI agents such as Claude Code, GitHub Copilot, Codex CLI, and Gemini CLI read the graph to find context in one step instead of re-exploring the codebase on every task.

AI coding agents forget everything between sessions. Every task starts with the same expensive ritual: list directories, grep for symbols, read files, and rebuild a mental model that was already built the day before. Akemi removes that step. A scanner condenses the codebase into a graph of YAML nodes (modules, classes, functions, APIs, requirements, decisions) connected by typed relations, and an index maps every source path to its node, so an agent loads exactly the context it needs in one read.

Because the graph is plain text committed next to the code, it is versioned, diffable, and reviewable like any other file. There is nothing to host and nothing to sync: one runtime dependency (PyYAML), a private venv inside `.akemi/`, and a validator that keeps nodes, relations, and the index honest as the code evolves. The same graph also carries requirements, architecture decision records, and SAFe work items, so an agent can walk from a user story to the exact functions it touches.

## How it works

1. A scanner walks the codebase and detects languages, modules, and symbols.
2. Each artifact (module, file, class, function, API, ...) becomes one YAML node under `.akemi/graph/nodes/<kind>/`.
3. An index (`.akemi/graph/index.yaml`) maps source paths to node files so agents can find context in one read.
4. Markdown views (architecture, api-surface, dependency-tree, ...) are generated from the graph.
5. A validator checks node schemas, relation targets, and index freshness.

```
.akemi/
  akemi.yaml          # config
  graph/
    index.yaml        # path -> node lookup
    nodes/<kind>/     # one YAML file per node
    views/            # generated markdown views
  guidelines/         # coding, testing, docs, graph maintenance
  templates/node/     # blank node per kind
  agents/             # per-agent integration assets
  runs/               # orchestration run ledger (agent-to-agent state)
  scripts/            # bootstrap, validate, heal, rebuild-index, rebuild-views
  python/             # the akemi package (installed into .akemi/.venv)
```

## Requirements

- Python >= 3.10
- git
- bash (macOS/Linux out of the box; on Windows only needed for the `.sh` wrappers, available via Git Bash)

Single runtime dependency: PyYAML. Optional extra `parsers` adds tree-sitter grammars for more accurate TypeScript/JavaScript scanning:

```bash
.akemi/.venv/bin/pip install '.akemi/python/[parsers]'
```

## Quick start

macOS / Linux:

```bash
git clone <this-repo> akemi
cd akemi
./src/scripts/install.sh /path/to/your/project
```

Windows (PowerShell or cmd, no bash required):

```powershell
git clone <this-repo> akemi
cd akemi
python src\scripts\install.py C:\path\to\your\project
```

`install.py` is a portable Python installer that accepts the same options as `install.sh` except `--ssh`; it also works on macOS and Linux. The installer creates `.akemi/` in the target project, copies the skeleton and the Python package, builds a private venv at `.akemi/.venv` (`bin/` on POSIX, `Scripts\` on Windows), configures the agent integration (Claude Code by default), and bootstraps the graph: it scans the codebase, writes the nodes, builds the index, and generates the views. Use `--skip-bootstrap` to create the structure without scanning, and `--dry-run` to preview.

### Let your coding agent install it

You can hand the whole installation to the AI agent you already use. Clone Akemi, start your coding CLI inside the clone, and ask for the install:

```bash
git clone https://github.com/fabianvaccaro/akemi.git
cd akemi
claude   # or codex, gemini, or any CLI that reads AGENTS.md
```

Then prompt:

> Read the project guidelines and install Akemi into /path/to/my/project. Set it up for Claude Code, GitHub Copilot, and Gemini CLI.

The repository ships agent instructions ([AGENTS.md](AGENTS.md), mirrored for Claude Code, Gemini, and Copilot) that tell the agent how to run the installer, configure every requested AI integration, verify the result with the validator, and report back. Listing several agents in one prompt is fine; the instructions cover multi-agent setup.

## Agent setup

### Claude Code

```bash
./src/scripts/install.sh --agent claude /path/to/project
```

Installs Akemi rules, skills, commands, and subagents under `.akemi/agents/claude/` and syncs them into the project's `.claude/` directory (`rules/`, `skills/`, `commands/`, `agents/`). Hooks are merged into `.claude/settings.json` to mark the index stale after edits. The project's `CLAUDE.md` gets one import line:

```
@.akemi/agents/claude/CLAUDE.md
```

### GitHub Copilot

```bash
./src/scripts/install.sh --agent copilot /path/to/project
```

Writes a graph-first instruction block to `.github/copilot-instructions.md`. If the file already exists, the block is appended once (guarded by an `<!-- akemi -->` marker).

### Codex CLI

```bash
./src/scripts/install.sh --agent codex /path/to/project
```

Writes the same instruction block to `AGENTS.md` at the project root, with the same marker-based append logic.

### Gemini CLI

```bash
./src/scripts/install.sh --agent gemini /path/to/project
```

Writes the same instruction block to `GEMINI.md` at the project root, with the same marker-based append logic.

## Daily use

All commands run from the project root:

```bash
.akemi/scripts/bootstrap.sh .        # full scan; first install or after large refactors
.akemi/scripts/validate.sh           # check graph integrity; run after every change set
.akemi/scripts/heal.sh               # fix mechanical issues: IDs, moved paths, deleted files
.akemi/scripts/rebuild-index.sh      # refresh index.yaml after adding/moving nodes
.akemi/scripts/rebuild-views.sh      # regenerate markdown views from the graph
```

On Windows every wrapper also ships as a `.cmd` file for PowerShell and cmd:

```powershell
.akemi\scripts\validate.cmd
.akemi\scripts\rebuild-index.cmd
```

The `.sh` wrappers also run under Git Bash on Windows (Claude Code uses Git Bash there, so agent instructions referencing `bash .akemi/scripts/*.sh` work unchanged). Both wrapper sets delegate to the same Python package; you can call it directly with `.akemi/.venv/bin/python -m akemi <command>` (POSIX) or `.akemi\.venv\Scripts\python.exe -m akemi <command>` (Windows).

Typical loop: the agent reads `index.yaml`, edits code, updates the touched nodes, then runs `validate.sh`. Rebuild the index when nodes are added or renamed, and rebuild views before reviewing architecture.

## Design proposals

The `akemi-propose` skill (installed with the Claude Code integration) turns a one-line idea into a reviewed design document:

```
/akemi-propose payment retry policy for the billing module
```

The workflow runs seven stages in order: research the graph, draft the design, architecture review against existing ADRs, a risk-ordered test plan, persistence to the graph, a self-verification gate, and the final report. The output is a proposal document at `.akemi/docs/proposals/<topic>.md` plus a `doc` node, and `adr` nodes drafted as `proposed` whenever the design sets a new lasting decision.

Two properties make the result trustworthy:

- Compliant by design. Every artifact is created from the node templates, linked with canonical relations, and the workflow does not finish until `validate.sh` reports zero errors.
- Self-verified. Before presenting, the skill checks its own output: every cited node ID exists in the index, every ADR constraint is satisfied or explicitly superseded, every acceptance criterion has a planned test and every planned test maps back to a criterion, the impact list matches the dependency edges in the graph, and new dependencies carry permissive licenses. Checks that still fail after revision are reported under "Open issues", never hidden.

The test plan is derived from acceptance criteria and risk (business value of the work item times the dependency blast radius of the touched nodes), not from file lists. Tests for getters, framework behavior, configuration, or bare coverage numbers are explicitly rejected.

After approval, `/akemi-plan` decomposes the proposal into epics, features, stories, and tasks.

## Orchestrated runs and self-healing

Multi-step work can be coordinated through a run ledger: one YAML file per task at `.akemi/runs/run-<slug>.yaml` (schema in `.akemi/runs/SCHEMA.md`). The run file records the step plan, which agent owns each step, the handoff each agent wrote back (nodes touched, summary, validation result, blockers), and an independent verification verdict per step. It is the only agent-to-agent channel that survives session loss: `/akemi-run run-<slug>` resumes exactly where the ledger says work stopped.

Three roles keep the ledger honest. The orchestrator owns the run status and the step plan. Each specialist agent writes only its own step's handoff. The auditor agent (Akemi-Auditor) writes the verification blocks, checking every handoff claim against the graph, the git diff, and the test suite. A step counts as complete when it is verified, never when the agent that did the work says it is done.

Self-healing splits the same way. Mechanical problems with one correct answer (a node ID that does not match its filename, a path pointing at a moved or deleted file, refs broken by a rename) are fixed deterministically by `heal.sh`, which then rebuilds the index; `--dry-run` previews the fixes. Judgment problems are surfaced by `/akemi-audit`, which heals first and then audits plans (hierarchy, acceptance criteria, test tasks, WSJF, status consistency), proposals (the same verification gate `/akemi-propose` runs), run ledgers, and node bodies against the real code, routing each finding to the agent that owns it. Run validation is part of `validate.sh` (check #10), so broken run references fail the same gate as broken graph references.

## Prompting guide

Akemi works best when prompts point the agent at the graph instead of the raw source tree.

**Read the graph first.** Ask for structure through the graph, not by scanning files:

> Read the akemi graph and summarize the architecture of the payments domain.

The agent reads `views/architecture.md`, then the index, then only the node bodies it needs. One read instead of a directory crawl.

**Locate before editing.**

> Using the akemi index, find every node that depends on cls-user-service and show the impact of changing its public methods.

**Check compliance.** Say "check akemi compliance" or run `/akemi-validate`. The agent runs the validator and drives FAIL lines to zero. Do this after every merge or large edit session.

**Keep the graph in sync.** End edit sessions with "update the akemi graph for the changes we just made" or `/akemi-update`. The hooks mark the index stale automatically, but node bodies and relations are the agent's job.

**Propose, then plan.**

> /akemi-propose rate limiting for the public API

then, after approving the proposal, `/akemi-plan` to turn it into backlog items.

**Work across repositories.** Any directory with a `.akemi/` graph can be read by an agent working in another project. Grant access first (Claude Code: `/add-dir /path/to/other-repo`, or start with `claude --add-dir /path/to/other-repo`), then point the prompt at the graph:

> The repo at /path/to/other-repo is governed by akemi. Read its .akemi/graph/views/architecture.md and index.yaml, and tell me which API nodes our client should call.

Read the other project's views and index instead of its source; they are designed to be consumed cross-repo without loading the codebase. Scripts always operate on the repo that contains them, so never run another repo's `.akemi/scripts/` against your own project.

**Anti-patterns.** Do not ask the agent to grep the codebase for structure the index already maps. Do not edit `index.yaml` or `views/*.md` by hand; they are generated. Do not code without a task or story node when SAFe mode is in use.

## Node kinds

| Kind | Describes |
|---|---|
| domain | A bounded business or technical area |
| module | A package, service, or build unit |
| file | A single source file |
| class | A class or struct |
| interface | An interface, protocol, or trait |
| function | A standalone function |
| api | An exposed endpoint or public API surface |
| resource | An external resource (queue, bucket, table) |
| requirement | A product or technical requirement |
| adr | An architecture decision record |
| technology | A framework, library, or tool in use |
| test | A test suite or notable test file |
| doc | A documentation artifact |
| config | A configuration file or setting group |
| epic | Top-level SAFe work item |
| capability | Large solution-level work under an epic |
| feature | Releasable functionality under a capability |
| story | User story under a feature |
| task | Implementation task |
| bug | Defect work item |
| pi | Program increment (planning interval) |
| iteration | Sprint within a PI |
| objective | PI objective |

Work-item hierarchy: epic > capability > feature > story. Relations: `realizes` (child work item to its parent: story -> feature -> capability -> epic), `planned_for` (story -> iteration), `part_of` (task -> story, iteration -> pi).

## Supported languages

- Python: stdlib `ast`, no extra dependencies
- TypeScript / JavaScript: regex scanner by default; install the `parsers` extra for tree-sitter accuracy
- Java and Scala: project detection via Maven, Gradle, and sbt build files; regex scanners for symbols

## SAFe work items

Akemi models SAFe work items as graph nodes like any other kind: an epic breaks into capabilities, then features, then stories, with tasks and bugs attached where they occur. Stories link to the code and test nodes they touch, so a reviewer can walk from a PI objective to the exact files involved. Planning state lives in `planned_for` relations to `iteration` nodes and WSJF fields on epics, capabilities, and features. The generated `backlog.md` view under `.akemi/graph/views/` renders the current hierarchy and PI assignments. Conventions and ceremonies are documented in `.akemi/guidelines/safe-scrum.md`.

## FAQ

### Does Akemi need a database or a server?

No. The graph is plain YAML files committed inside the repository. There is no database, no embeddings, no vector store, and no server process. The only runtime dependency is PyYAML.

### Which AI coding agents does Akemi support?

Claude Code gets the deepest integration (rules, skills, slash commands, subagents, and hooks). GitHub Copilot, Codex CLI, and Gemini CLI get a graph-first instruction block in the file each one reads (`.github/copilot-instructions.md`, `AGENTS.md`, `GEMINI.md`). One project can be set up for several agents at once.

### How is this different from a CLAUDE.md file or editor rules?

Instruction files tell an agent how to behave; they do not tell it what the codebase contains. Akemi adds a structured, validated map of the code itself: every module, class, function, and API is a node with typed relations, and an index resolves any source path to its node. The instruction files Akemi installs simply point the agent at that map.

### Does it work on Windows?

Yes. `install.py` and the `.cmd` wrappers run from PowerShell or cmd with no bash required, and the `.sh` wrappers work under Git Bash. All logic lives in the Python package, so both wrapper sets do the same thing.

### What happens when the code changes?

Hooks mark the index stale automatically after edits. The agent updates the touched nodes, then `validate.sh` checks node schemas, relation targets, and index freshness. `bootstrap.sh` rescans everything after large refactors.

### Can I use the graph from another repository?

Yes. Views and the index are designed to be read cross-repo: grant the agent access to the other repository and point it at `.akemi/graph/views/` and `index.yaml` instead of the source tree.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming, commit conventions, versioning, and the release process. Release history lives in [CHANGELOG.md](CHANGELOG.md).

## License

MIT. All dependencies are permissively licensed (MIT/BSD/Apache 2.0); no copyleft.
