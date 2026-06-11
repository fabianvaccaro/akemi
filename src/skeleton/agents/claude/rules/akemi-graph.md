---
globs: .akemi/graph/**/*.yaml
---
# Akemi Graph Node Rules

When editing files under `.akemi/graph/nodes/`:

1. Node file is under 120 lines
2. `id` field equals filename without `.yaml`
3. Every `refs[].to` is an existing node ID (check `.akemi/graph/index.yaml`; if `.akemi/.index-stale` exists, run `bash .akemi/scripts/rebuild-index.sh` first)
4. ID prefix matches kind: dom-, mod-, file-, cls-, iface-, fn-, api-, res-, req-, adr-, tech-, test-, doc-, cfg-, epic-, cap-, feat-, story-, task-, bug-, pi-, iter-, obj-
5. `rel` values are canonical: part_of, extends, implements, depends_on, tests, realizes, planned_for, affects, supported_by, uses_technology (plus template-defined rels like tested_by, provided_by)
6. Body explains WHY, not WHAT. Max 20 lines of markdown
7. `updated` set to today's date on every modification
8. Never delete a node file. Set `status: deprecated` instead. Never reuse a deprecated ID
9. Never edit `.akemi/graph/index.yaml` or `.akemi/graph/views/*` directly: they are generated
10. After editing nodes: `bash .akemi/scripts/rebuild-index.sh` then `bash .akemi/scripts/validate.sh`. If validate prints FAIL, fix the named nodes and re-run (max 3 attempts, then report the FAIL output verbatim)
