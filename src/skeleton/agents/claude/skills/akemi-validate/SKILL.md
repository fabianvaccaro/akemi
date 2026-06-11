---
name: akemi-validate
description: "Validate the Akemi graph for broken references, orphan nodes, line count violations, and missing coverage."
tools: Read, Glob, Grep, Bash
user-invocable: true
---

Validate Akemi graph integrity.

## Checks

1. **Broken References**: All `refs[].to` in node files point to existing node IDs in index

2. **Orphan Nodes**: Find nodes with zero incoming AND zero outgoing refs (except domain nodes - top-level)

3. **Stale Paths**: For file/class/function/test/doc/config nodes, verify `path` field points to existing file on disk

4. **Line Count**: All node files under 120 lines

5. **Missing Nodes**: Scan `src/` for files without graph nodes

6. **Test Coverage**: Find class/function nodes without `tested_by` refs

7. **Interface Compliance**: Find class nodes without `implements` refs

8. **ID Consistency**: Node `id` field matches filename

## Output Format

```
PASS  | Broken references: 0 found
FAIL  | Orphan nodes: 3 found (cls-old-service, fn-unused, doc-draft)
WARN  | Missing nodes: 5 source files without graph nodes
PASS  | Line count: all nodes under 120 lines
FAIL  | Test coverage: 4 classes without test refs
WARN  | Interface compliance: 2 classes without interface refs
```

## After Validation

Report results. FAIL items → suggest fixes. WARN items → note for future.