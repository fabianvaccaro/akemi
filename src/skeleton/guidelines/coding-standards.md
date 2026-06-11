# Akemi Coding Standards

## Object-Oriented Programming by Default

- Every logical unit = class, single responsibility
- Public classes MUST have interface
- Constructor DI for all deps
- Never `new` deps inside class
- Composition over inheritance
- Static methods only for pure utils

## File Size Limits

- **Source files**: Max 300 lines. Split at 250 proactive
- **Graph nodes**: Max 120 lines
- **Test files**: Max 400 lines (tests need setup space)
- File over limit → Akemi-Refactorer splits

## Modularization

- Vertical slices by feature/domain, not horizontal layers
- Each module = directory under `src/`
- Each module has one domain parent in graph
- Module deps form DAG, no cycles
- Cross-module via interfaces

## Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Files | kebab-case | `user-service.ts` |
| Classes | PascalCase | `UserService` |
| Interfaces | PascalCase with I prefix | `IUserService` |
| Functions | camelCase | `validateToken` |
| Variables | camelCase | `accessToken` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Graph IDs | prefix-kebab-case | `cls-user-service` |

### Language-Specific Naming (Monorepo Projects)

Monorepo: naming follows workspace language convention.

| Language | Functions | Variables | Files |
|----------|-----------|-----------|-------|
| TypeScript/JavaScript | camelCase | camelCase | kebab-case.ts |
| Python | snake_case | snake_case | snake_case.py |
| Go | camelCase (exported: PascalCase) | camelCase | lowercase.go |
| Rust | snake_case | snake_case | snake_case.rs |
| Java/Kotlin | camelCase | camelCase | PascalCase.java |

## File Naming Rules

- No bare `index.ts`. Descriptive: `user-service.ts`
- No `utils.ts` / `helpers.ts`. Name by function: `string-formatters.ts`
- Test files mirror source: `src/auth/service.ts` -> `tests/unit/auth/service.test.ts`
- One class per file. Filename matches class name (kebab-case)

## Code Organization Within Files

```
1. Imports (grouped: external, internal, types)
2. Interface/type definitions
3. Class definition
   a. Properties
   b. Constructor
   c. Public methods
   d. Private methods
4. Standalone exports (if any)
```

## Error Handling

- Typed error classes, not generic Error
- Validate at system boundaries (API input, external data)
- Trust internal interfaces, no re-validate between modules
- Errors propagate up; catch only when can handle

## Dependencies

- All deps declared in constructor
- Interfaces for internal deps (enables testing)
- External libs via wrapper classes (enables swap)