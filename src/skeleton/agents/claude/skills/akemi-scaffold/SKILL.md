---
name: akemi-scaffold
description: "Scaffold new code with graph nodes. Usage: /akemi-scaffold <kind> <name> [module]"
tools: Read, Write, Edit, Glob, Grep, Bash
user-invocable: true
---

Scaffold new code files + graph nodes.

## Process

1. Parse $ARGUMENTS for `<kind>`, `<name>`, optional `[module]`
   Kinds: service, repository, controller, entity, dto

2. Read `.akemi/akemi.yaml` for language + conventions.
   If `type: monorepo` with `workspaces:`, find which workspace owns target module
   (match module path vs workspace `root:` values). Use that workspace's language +
   framework.

3. Pick parent module:
   - If `[module]` given, use it
   - Else ask user

4. Read graph index for existing module structure

5. Create source files (paths by project type):
   - Single-language: `src/<module>/...`
   - Monorepo: `<workspace_root>/src/<module>/...` or `<workspace_root>/<module>/...`
   Files:
   - Interface: `<base>/<module>/interfaces/<name>.interface.<ext>`
   - Impl: `<base>/<module>/<name>.<kind>.<ext>`
   - Test: `<test_dir>/<module>/<name>.<kind>.test.<ext>`

6. Create graph nodes per file:
   - Interface node (iface-<name>)
   - Class node (cls-<name>-<kind>)
   - Test node (test-<name>-<kind>)
   - Update parent module node refs

7. Apply Akemi standards:
   - Constructor DI in impl
   - Implement interface
   - Test scaffold with describe/it blocks

8. Rebuild:
   ```bash
   bash .akemi/scripts/rebuild-index.sh
   bash .akemi/scripts/rebuild-views.sh
   ```