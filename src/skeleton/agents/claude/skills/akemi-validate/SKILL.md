---
name: akemi-validate
description: "Validate the Akemi graph and fix what fails. Checks references, orphans, stale paths, line counts, and coverage."
tools: Read, Edit, Glob, Grep, Bash
user-invocable: true
---

Run the validator and drive failures to zero.

## Steps

1. Heal the mechanical layer first, then validate:
   ```bash
   bash .akemi/scripts/heal.sh
   bash .akemi/scripts/validate.sh
   ```
   Heal fixes ID mismatches, repoints moved files, deprecates nodes for deleted
   files, and rebuilds the index; its MANUAL lines need the fix loop below.
   The script prints one line per check: `PASS | ...`, `FAIL | ...`, or `WARN | ...`.
   If the script itself is missing or exits with an error (not FAIL lines), report the exact command and stderr and stop; do not improvise checks by hand.

2. All PASS: report "validation clean" and stop.

## Fix Loop (max 3 attempts)

For each FAIL line, fix the named nodes by editing their YAML under `.akemi/graph/nodes/` only. Never edit `index.yaml` or `views/*.md`: they are generated.

| FAIL | Fix |
|------|-----|
| Broken reference | Point `refs[].to` at an existing ID, or create the missing node from `.akemi/templates/node/` |
| Orphan node | Add the real relationship (usually `part_of` its module/story), or `status: deprecated` if obsolete |
| Stale path | Update the node's `path` to the file's new location; file truly gone: `status: deprecated` |
| Line count > 120 | Trim the markdown body (keep WHY, cut WHAT) |
| ID mismatch | Make the `id` field equal the filename without `.yaml` |
| Missing nodes | Create nodes for the listed source files (see /akemi-update) |
| Missing test refs | Route to Akemi-Tester; or add `tested_by` if the test exists |

After fixing, rebuild and re-run:
```bash
bash .akemi/scripts/rebuild-index.sh
bash .akemi/scripts/validate.sh
```

Still FAIL after 3 attempts: stop. Report the remaining FAIL lines verbatim plus what you tried. Do not keep looping.

## WARN Items

Do not block on WARN. List them with the responsible agent (coverage -> Akemi-Tester, missing nodes -> Akemi-Documenter, interfaces -> Akemi-Developer).

Report one line: checks passed/failed, nodes fixed, remaining issues.
