---
description: "Visualize the Akemi graph as text"
---

Read `.akemi/graph/index.yaml`. Render graph as text diagram.

## Output Format

```
Domains & Modules:
  dom-identity
    ├── mod-auth
    │   ├── cls-auth-service (implements iface-auth-provider)
    │   ├── cls-token-manager
    │   └── fn-hash-password
    └── mod-rbac
        └── cls-role-service

  dom-billing
    └── mod-billing
        ├── cls-billing-service
        └── cls-invoice-generator

Dependencies:
  mod-auth ──depends_on──> mod-database
  mod-billing ──depends_on──> mod-auth, mod-database

APIs:
  POST /auth/login (api-auth-login) ──provided_by──> mod-auth
  GET /billing/plans (api-billing-plans) ──provided_by──> mod-billing

Resources:
  res-primary-db
    ├── res-users-table
    └── res-billing-table
```

Show full graph topology. Group by domains, modules, entities.
Show key edges (dependencies, provides, consumes).
If $ARGUMENTS has node ID, show only that node neighborhood (1 hop).