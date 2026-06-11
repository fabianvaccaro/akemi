---
name: akemi-create-node
description: "Create a new Akemi graph node. Usage: /akemi-create-node <kind> <name>"
tools: Read, Write, Glob, Bash
user-invocable: true
---

Create a graph node from a template.

## Steps

1. Parse $ARGUMENTS for `<kind>` and `<name>`. Kind -> prefix:

   domain=dom, module=mod, file=file, class=cls, interface=iface, function=fn,
   api=api, resource=res, requirement=req, adr=adr, technology=tech, test=test,
   doc=doc, config=cfg, epic=epic, capability=cap, feature=feat, story=story,
   task=task, bug=bug, pi=pi, iteration=iter, objective=obj

2. Build the ID: `<prefix>-<kebab-case-name>` (e.g. `cls-user-service`, `feat-sso-login`)

3. If `.akemi/.index-stale` exists: `bash .akemi/scripts/rebuild-index.sh`.
   Then check `.akemi/graph/index.yaml`: the ID must not already exist. If it does, stop and report the existing node.

4. Read the template `.akemi/templates/node/<kind>.yaml`. If the template file is missing, report the path and stop; do not invent a schema.

5. Fill it in: replace every CHANGEME, set `created` and `updated` to today, remove ref lines that do not apply. Refs use canonical rels: part_of, extends, implements, depends_on, tests, realizes, planned_for, affects, supported_by, uses_technology. Every `refs[].to` must be an ID present in the index; ask the user when the right target is unclear.

   SAFe kinds: child `realizes` parent (cap->epic, feat->cap, story->feat); task `part_of` story; story `planned_for` iter-; iter `part_of` pi-; obj- `supported_by` feat-/story-.

6. Write to `.akemi/graph/nodes/<kind>/<id>.yaml`. Keep it under 120 lines; body explains WHY, max 20 lines.

7. Rebuild and check:
   ```bash
   bash .akemi/scripts/rebuild-index.sh
   bash .akemi/scripts/validate.sh
   ```
   If validate prints FAIL lines naming your node, fix the YAML and re-run (max 3 attempts, then report the FAIL output verbatim).

8. Report one line: node ID created, validation result.
