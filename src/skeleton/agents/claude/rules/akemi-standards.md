---
globs: "{src,app,lib,backend,frontend,server,api,services,scripts,mcp-server}/**/*"
---
# Akemi Development Standards - MANDATORY

**Monorepo note**: Monorepo projects (`type: monorepo` in akemi.yaml), each workspace
may differ language conventions. Check workspace config for file editing.
Python workspaces use `snake_case` files/functions; TypeScript workspaces use `kebab-case` files
+ `camelCase` functions.

Creating/modifying source code, MUST:

1. **OOP by default**: Classes, single responsibility. Public class needs interface
2. **Max 300 lines per file**: Split at 250. Use Akemi-Refactorer if needed
3. **Constructor DI**: Inject deps via constructor. Never `new` for internal deps
4. **Naming**: Files kebab-case, classes PascalCase. Function naming follows workspace
   language convention (camelCase JS/TS, snake_case Python/Rust, etc.)
5. **No bare index files**: Descriptive names (`user-service.ts`, not `index.ts`)
6. **Tests required**: Every public class/function needs unit test. Target 90%+ coverage
7. **Graph nodes required**: After new files, create graph nodes in `.akemi/graph/nodes/`
8. **Vertical slices**: Organize by feature/domain, not layer
9. **Read graph FIRST**: Before modifying file, check `.akemi/graph/index.yaml` for node + deps
10. **Use Akemi agents**: Route work through appropriate Akemi-* agent, not generic coding