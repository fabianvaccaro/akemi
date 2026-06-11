---
description: "Show Akemi graph health metrics and status"
---

Read `.akemi/graph/index.yaml`. Report:

1. **Node counts** by kind (table format)
2. **Graph stats**: total nodes, total edges
3. **Staleness**: check `.akemi/.index-stale` exists
4. **Last rebuild**: show `generated` timestamp from index
5. **Health checks** (quick):
   - Count modules no test coverage (no `tested_by` in edges)
   - Count API nodes no `documented_by` edges
   - Count nodes `status` != `active`
6. **Standards compliance**:
   - Read `.akemi/akemi.yaml` for configured standards
   - Report configured coverage threshold + file limits

Output: concise dashboard.