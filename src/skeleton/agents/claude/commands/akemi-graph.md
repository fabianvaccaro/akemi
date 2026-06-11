---
description: "Visualize the Akemi graph as text"
---

Render the graph topology from `.akemi/graph/index.yaml`.
If `.akemi/.index-stale` exists, run `bash .akemi/scripts/rebuild-index.sh` first.
If `index.yaml` is missing, suggest `bash .akemi/scripts/bootstrap.sh` and stop.

If $ARGUMENTS contains a node ID, show only that node's 1-hop neighborhood
(incoming and outgoing edges with rel names). Otherwise show the full topology:

```
Domains & Modules:
  dom-identity
    mod-auth
      cls-auth-service (implements iface-auth-provider)
      fn-hash-password
    mod-rbac
      cls-role-service

Dependencies:
  mod-auth --depends_on--> mod-database
  mod-billing --depends_on--> mod-auth, mod-database

APIs:
  POST /auth/login (api-auth-login) --part_of--> mod-auth

Resources:
  res-primary-db
    res-users-table

Backlog (if work item nodes exist):
  epic-auth <--realizes-- cap-sso <--realizes-- feat-saml <--realizes-- story-saml-login
```

Group by domain, then module. Show key edges (depends_on, implements, realizes).
Mark deprecated nodes with `[deprecated]`. ASCII only.
