---
name: akemi-scaffold
description: "Scaffold new code with graph nodes. Usage: /akemi-scaffold <kind> <name> [module]"
tools: Read, Write, Edit, Glob, Grep, Bash
user-invocable: true
---

Scaffold source files plus their graph nodes in one pass.

## Steps

1. Parse $ARGUMENTS for `<kind>` (service, repository, controller, entity, dto), `<name>`, optional `[module]`.

2. Read `.akemi/akemi.yaml` for language and conventions. If `type: monorepo`, match the target module against workspace `root:` values and use that workspace's language and framework (typescript, python, java, scala, ...) and its test framework.

3. Resolve the parent module: use `[module]` if given, else list mod- nodes from `.akemi/graph/index.yaml` and ask the user. If `.akemi/.index-stale` exists, run `bash .akemi/scripts/rebuild-index.sh` first.

4. Create source files using the workspace's layout and extension:
   - Interface: `<base>/<module>/interfaces/<name>.interface.<ext>` (Java/Scala: `I<Name>` or trait in the package dir)
   - Implementation: `<base>/<module>/<name>.<kind>.<ext>` implementing the interface, constructor DI, no internal `new`
   - Test: `<test_dir>/<module>/<name>.<kind>.test.<ext>` (or src/test/... for maven/gradle/sbt) with describe/it or class-per-method skeleton

5. Create one node per file in `.akemi/graph/nodes/`:
   - `iface-<name>` with `{ rel: part_of, to: mod-<module> }`
   - `cls-<name>-<kind>` with `part_of` module, `implements` the interface, `depends_on` injected deps, `tested_by` the test node
   - `test-<name>-<kind>` with `{ rel: tests, to: cls-<name>-<kind> }`

6. Rebuild and check:
   ```bash
   bash .akemi/scripts/rebuild-index.sh
   bash .akemi/scripts/rebuild-views.sh
   bash .akemi/scripts/validate.sh
   ```
   FAIL lines naming your nodes: fix the YAML, re-run, max 3 attempts, then report the FAIL output verbatim.

## Failure Handling

- Parent module node missing: offer to create `mod-<module>` first; do not attach refs to nonexistent IDs.
- Template or script missing: report the exact path/command and stderr; do not improvise.

Report one line: files created, nodes created, validation result.
