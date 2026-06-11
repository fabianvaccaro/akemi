# Akemi Documentation Standards

## Graph Node Documentation

Every significant code entity needs graph node. "Significant" means:
- All modules (directories under `src/`)
- All classes and interfaces
- All API endpoints
- All database tables and external resources
- All standalone exported functions
- All test suites

## Node Body Writing Rules

- Describe **WHY**, not **WHAT** (code shows what)
- Max 20 lines markdown in body
- Plain language, no jargon without explanation
- Reference related nodes by ID, not description

### Good Node Body

```
Handles JWT validation for stateless auth across services.
Chosen over session-based auth per ADR-003 to eliminate
shared state between API servers.
```

### Bad Node Body

```
This class has a validateToken method that takes a token
string and calls jwt.verify to check the signature and
expiration date, then queries the database for the user.
```

## Architecture Decision Records

Every non-trivial architecture decision gets ADR node:
- Technology choices (database, framework, library)
- Pattern choices (event sourcing, CQRS, REST vs GraphQL)
- Module boundary changes
- Security architecture decisions

ADR format: Context -> Decision -> Consequences

## Documentation Files

User-facing docs (guides, API references):
- Create doc graph node linking to file
- Keep docs in `docs/` directory
- Reference implementation nodes via graph edges

## Canonical Edge Types

| Edge | Inverse | Usage |
|------|---------|-------|
| part_of | contains | Structural containment |
| extends | extended_by | Class/interface inheritance |
| implements | implemented_by | Class implements interface |
| depends_on | - | Module/class dependency |
| tested_by | tests | Entity has test coverage |
| imports | - | File-level import |
| uses_technology | used_by | Module uses a technology |
| calls | called_by | Function/API call |
| documents | documented_by | Documentation link |
| configures | - | Config targets a resource |
| consumes | consumed_by | Resource consumption |
| provides | provided_by | API provision |
| addresses | addressed_by | Requirement/ADR link |
| impacts | - | ADR impacts a module |
| breaks_into | - | Story breaks into tasks |
| affects | - | Bug affects an entity |
| fixed_by | - | Bug fixed by a task |

## Keeping Documentation Current

- Graph nodes updated alongside code changes
- Views regenerated after index rebuilds
- Stale nodes flagged by `/akemi-validate`
- Deprecated entities keep nodes with `status: deprecated`