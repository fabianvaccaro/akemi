---
name: akemi-update
description: "Update the Akemi graph after code changes. Use when files have been created, modified, renamed, moved, or deleted."
tools: Read, Write, Edit, Glob, Grep, Bash
user-invocable: true
---

Update Akemi graph. Reflect recent code changes.

## Process

1. Read `.akemi/graph/index.yaml`. Get current state.

2. For each file created:
   - Pick node kind (file, class, interface, function, etc.)
   - Gen ID: `<prefix>-<kebab-case-name>`
   - Read template `.akemi/templates/node/<kind>.yaml`
   - Fill: id, name, path, language, refs (part_of, extends, implements, etc.)
   - Write `.akemi/graph/nodes/<kind>/<id>.yaml`

3. For each file modified:
   - Find node via index
   - Update: loc, refs, updated date
   - Node missing → create

4. For each file deleted:
   - Find node via index
   - Set `status: deprecated` (do NOT delete node file)

5. Update cross-refs in affected nodes (add/remove refs)

6. Change affects user flow → update journey file
   `.akemi/journeys/` (states, transitions, graph_refs, backend_processes)

7. Rebuild:
   ```bash
   bash .akemi/scripts/rebuild-index.sh
   bash .akemi/scripts/rebuild-views.sh
   ```

8. Verify node files <120 lines

## ID Prefixes

dom, mod, file, cls, iface, fn, api, res, req, adr, tech, test, doc, cfg