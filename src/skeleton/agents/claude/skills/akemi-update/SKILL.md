---
name: akemi-update
description: "Update the Akemi graph after code changes. Use when files have been created, modified, renamed, moved, or deleted."
tools: Read, Write, Edit, Glob, Grep, Bash
user-invocable: true
---

Sync the graph with recent code changes. Run this after any edit session.

## Steps

1. If `.akemi/.index-stale` exists: `bash .akemi/scripts/rebuild-index.sh`.
   Read `.akemi/graph/index.yaml` for current state. List changed files (`git status --short` or from context).

2. Created files: pick the kind (file, class, interface, function, test, config), build the ID `<prefix>-<kebab-case-name>`, fill `.akemi/templates/node/<kind>.yaml` (id, name, path, language, refs: `part_of` module, `implements`, `extends`, `depends_on`, `uses_technology`), write to `.akemi/graph/nodes/<kind>/<id>.yaml`.

3. Modified files: find the node via the index path lookup; update refs to match real imports/deps and set `updated` to today. No node found: create one as in step 2.

4. Moved/renamed files: update the node's `path`, keep the same ID.

5. Deleted files: set the node's `status: deprecated`. Never delete node files; never reuse the ID.

6. Fix cross-refs in affected nodes (add/remove `depends_on` etc.). Every `refs[].to` must exist in the index.

7. Work item linkage: if the change completes a task, update the task node status; if a user flow changed, update the journey YAML in `.akemi/journeys/`.

8. Rebuild and check:
   ```bash
   bash .akemi/scripts/rebuild-index.sh
   bash .akemi/scripts/rebuild-views.sh
   bash .akemi/scripts/validate.sh
   ```
   FAIL lines: fix the named node YAML, re-run, max 3 attempts, then report the remaining FAIL output verbatim and stop.

## Rules

- Never edit `index.yaml` or `views/*.md` by hand; they are generated from node files.
- Node files under 120 lines; bodies WHY not WHAT.
- Prefixes: dom, mod, file, cls, iface, fn, api, res, req, adr, tech, test, doc, cfg, epic, cap, feat, story, task, bug, pi, iter, obj.

Report one line: nodes created/updated/deprecated, validation result.
