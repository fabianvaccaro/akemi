# Akemi

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](src/python/pyproject.toml)
[![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#requirements)

Graph-based codebase documentation for AI coding agents. Akemi keeps the structure of your project as a knowledge graph of plain YAML nodes and relations inside the repository, with no database and no server. AI agents such as Claude Code, GitHub Copilot, Codex CLI, and Gemini CLI read the graph to find context in one step instead of re-exploring the codebase on every task.

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
  scripts/            # bootstrap, validate, rebuild-index, rebuild-views
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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming, commit conventions, versioning, and the release process. Release history lives in [CHANGELOG.md](CHANGELOG.md).

## License

MIT. All dependencies are permissively licensed (MIT/BSD/Apache 2.0); no copyleft.
