# Changelog

All notable changes to Akemi are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-12

### Added

- `akemi heal` subcommand with `heal.sh` and `heal.cmd` wrappers: deterministic
  self-healing of mechanical graph issues. Rewrites node IDs to match filenames
  and retargets refs across the graph, repoints nodes whose file moved (unique
  basename match under the scan roots), deprecates nodes whose file was deleted,
  and rebuilds the index. Issues that need judgment are reported as MANUAL;
  `--dry-run` previews the fixes.
- Run ledger for agent orchestration: plain YAML files at `.akemi/runs/run-*.yaml`
  (schema in `.akemi/runs/SCHEMA.md`, template `run-template.yaml`) recording
  the step plan, per-step agent handoffs (nodes touched, summary, validation,
  blockers), free-form agent-to-agent messages, and independent verification
  verdicts. The ledger survives session loss and is the canonical
  agent-to-agent channel.
- Validator check #10: run files are validated like the graph. Broken
  graph_refs, step inputs, handoff nodes, and step dependencies are errors;
  unknown statuses, verified steps without a verification block, and done runs
  with unfinished steps are warnings.
- `Akemi-Auditor` subagent: independent verification of plans, proposals,
  nodes, code, and run steps. Audits handoff claims against the graph, the git
  diff, and the test suite, writes the verification blocks in run files, and
  routes findings to the owning agent. Never verifies its own work and never
  fixes anything itself.
- `/akemi-run` command: start or resume an orchestrated run; every step is
  executed by its owning agent and independently verified before it counts.
- `/akemi-audit` skill: self-healing audit pipeline. Heals the mechanical
  layer, then audits plans (hierarchy, acceptance criteria, test tasks, WSJF,
  status consistency), proposals (the `/akemi-propose` verification gate),
  run ledgers, and node bodies against the real code.
- Claude Code rule for run files (`akemi-runs.md`): write ownership, canonical
  statuses, and lifecycle rules for the run ledger.

### Changed

- `Akemi-Orchestrator` coordinates through the run ledger: steps with explicit
  dependencies, handoffs written to the run file instead of conversation
  memory, independent verification by `Akemi-Auditor` before a step counts,
  and resumability after session loss.
- All specialist agents gained a run protocol section (read the assignment
  from the run file, write the handoff back) and now run `heal.sh` before
  hand-fixing validation failures.
- `/akemi-validate` heals before validating.
- Validator scan-root logic is shared between the validator and the healer.

## [0.1.0] - 2026-06-12

### Added

- Release automation: pushing a `v*` tag now checks that all version files
  agree with the tag and creates the GitHub release with the matching
  changelog section as the release notes.
- `akemi-propose` Claude Code skill: staged design proposal workflow with
  graph research, architecture review against existing ADRs, a risk-ordered
  test plan derived from acceptance criteria, and a self-verification gate
  that checks cited node IDs, ADR compliance, criteria-to-test mapping,
  impact completeness, dependency licenses, and validator status before the
  proposal is presented.
- README: design proposal section and a prompting guide covering graph-first
  prompts, compliance checks, graph sync, and cross-repository graph access.

## [0.0.1] - 2026-06-12

First public release.

### Added

- Graph-based codebase documentation: plain YAML nodes and relations stored
  inside the repository, no database and no server.
- 23 node kinds covering code (domain, module, file, class, interface,
  function, api, resource, technology, test, doc, config), decisions
  (requirement, adr), and SAFe work items (epic, capability, feature, story,
  task, bug, pi, iteration, objective).
- Codebase scanner with language detection for Python (stdlib ast),
  TypeScript and JavaScript (regex by default, tree-sitter via the optional
  `parsers` extra), Java and Scala (Maven, Gradle, sbt).
- Index builder mapping source paths to node files for one-read agent lookup.
- Generated markdown views: architecture, api-surface, test-coverage,
  dependency-tree, tech-stack, backlog.
- Graph validator checking references, schemas, stale paths, coverage,
  orphans, and SAFe hierarchy.
- Agent integrations: Claude Code (rules, skills, commands, subagents,
  hooks), GitHub Copilot, Codex CLI, Gemini CLI.
- POSIX installer (`install.sh`) with local and SSH modes, plus upgrade
  script (`upgrade.sh`).
- Cross-platform installer (`install.py`, Python stdlib only) for Windows,
  macOS, and Linux.
- Windows support: `.cmd` wrappers for every script, venv layout detection,
  platform-aware Claude Code hook command, UTF-8 file handling throughout.
- `akemi` console entry point and `python -m akemi` module interface with
  bootstrap, rebuild-index, rebuild-views, validate, and sync-claude
  subcommands.

[0.2.0]: https://github.com/fabianvaccaro/akemi/releases/tag/v0.2.0
[0.0.1]: https://github.com/fabianvaccaro/akemi/releases/tag/v0.0.1
