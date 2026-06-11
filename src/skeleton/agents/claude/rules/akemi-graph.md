---
globs: .akemi/graph/**/*.yaml
---
# Akemi Graph Node Rules

Editing graph node files:

1. File under 120 lines
2. `id` field match filename (no `.yaml`)
3. All `refs[].to` valid node IDs (check `index.yaml`)
4. Correct kind prefix: dom, mod, file, cls, iface, fn, api, res, req, adr, tech, test, doc, cfg
5. Body = WHY not WHAT. Max 20 lines markdown
6. Update `updated` date when modifying
7. After edit, run: `bash .akemi/scripts/rebuild-index.sh`
8. Never delete nodes. Set `status: deprecated` instead