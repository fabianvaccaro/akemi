# Changelog

All notable changes to Akemi are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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

[0.0.1]: https://github.com/fabianvaccaro/akemi/releases/tag/v0.0.1
