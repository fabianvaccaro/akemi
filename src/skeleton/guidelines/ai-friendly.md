# AI-Friendly Development Guide

## Token Efficiency

Every file AI reads costs tokens. Minimize waste:

- **Small files**: 300-line source limit = agents read less per file
- **Graph views first**: Architecture view ~50 tokens vs ~4000 for all nodes
- **Meaningful names**: Agents search by name. `user-service.ts` > `service.ts`
- **No deep nesting**: 2 levels max under `src/`
- **One class per file**: Agents read only what need

## Modular Architecture for AI

Vertical slice = AI-optimal:
- Feature self-contained (agent reads one dir)
- Dependencies explicit (graph edges)
- Changes localized (small blast radius)

```
# Good: Vertical slices
src/
  auth/
    auth.service.ts
    auth.controller.ts
    auth.repository.ts
    auth.interfaces.ts

# Bad: Horizontal layers
src/
  services/
    auth.service.ts     # Agent must read entire services/ to find auth
    billing.service.ts
  controllers/
    auth.controller.ts
```

## File Organization for Discoverability

- Names describe content: `jwt-validator.ts`, not `validator.ts`
- Group related files in feature dirs
- Barrel files only when 3+ public exports
- Short import paths: `@/auth/service` > `../../../auth/service`

## Code Patterns That Help AI

1. **Explicit over implicit**: Named params, return types, explicit imports
2. **Predictable structure**: Same layout across modules
3. **Self-documenting**: Good names cut comment need
4. **Interface-first**: Agents read interfaces to grasp contracts fast
5. **Pure functions**: Easier to reason about (no hidden state)

## Graph as AI Context

Akemi graph = structured context for AI:
- Index = full topology in one read
- Views = domain summaries, no YAML parsing
- Node bodies explain WHY (non-obvious part AI needs)
- Edge refs map dependency web agents navigate

## Anti-Patterns

- Large files (AI reads whole thing for one function)
- Deep inheritance (trace 5+ levels for behavior)
- Global state (can't track mutations across files)
- Magic strings/numbers (can't search undocumented constants)
- Circular deps (AI lost in infinite loops)
- Duplicate filenames (reads wrong file, wastes tokens)