---
name: akemi-create-node
description: "Create a new Akemi graph node. Usage: /akemi-create-node <kind> <name>"
tools: Read, Write, Glob
user-invocable: true
---

Create new graph node from template.

## Process

1. Parse $ARGUMENTS for `<kind>` and `<name>`
   Kinds: domain, module, file, class, interface, function, api, resource, requirement, adr, technology, test, doc, config, epic, story, task, bug

2. Map kind→prefix:
   domain=dom, module=mod, file=file, class=cls, interface=iface,
   function=fn, api=api, resource=res, requirement=req, adr=adr,
   technology=tech, test=test, doc=doc, config=cfg,
   epic=epic, story=story, task=task, bug=bug

3. Gen ID: `<prefix>-<kebab-case-name>`

4. Check `.akemi/graph/index.yaml`, verify ID unique

5. Read template `.akemi/templates/node/<kind>.yaml`

6. Fill template:
   - Replace CHANGEME with real values
   - Set `created` + `updated` to today
   - Ask user re: relationships to existing nodes

7. Write to `.akemi/graph/nodes/<kind>/<id>.yaml`

8. Verify file under 120 lines

9. Rebuild index:
   ```bash
   bash .akemi/scripts/rebuild-index.sh
   ```