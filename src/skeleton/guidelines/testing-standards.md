# Akemi Testing Standards

## Coverage Requirements

- **Minimum**: 90% line coverage across project
- **Target**: 95%+ for critical modules (auth, payments, data)
- CI pipeline MUST gate on coverage threshold
- Coverage measured per-module, aggregated

## Test Types

| Type | Scope | Location | Runner |
|------|-------|----------|--------|
| Unit | Single class/function | `tests/unit/` | Framework default |
| Integration | Module + dependencies | `tests/integration/` | Framework default |
| E2E | Full system | `tests/e2e/` | Framework default |

## Unit Test Rules

- One test file per source file
- Test behavior, not implementation
- One scenario per test
- Descriptive names: `should reject expired tokens`
- Mock external deps via interfaces
- Never mock class under test
- Arrange-Act-Assert pattern

## Test File Structure

```
describe('ClassName', () => {
  // Setup: create instance with mocked dependencies

  describe('methodName', () => {
    it('should handle happy path', () => {
      // Arrange -> Act -> Assert
    });

    it('should handle edge case', () => { ... });

    it('should throw on invalid input', () => { ... });
  });
});
```

## Test Naming Convention

- Test files: `<source-name>.test.<ext>` or `test_<source_name>.<ext>`
- Test suites: named after class/function tested
- Test cases: start with `should` + expected behavior

### Language-Specific Test Patterns (Monorepo Projects)

| Language | Test File Pattern | Test Structure |
|----------|------------------|----------------|
| TypeScript | `*.test.ts` | `describe/it` blocks |
| Python | `test_*.py` | `class TestX` or `def test_x` |
| Go | `*_test.go` | `func TestX(t *testing.T)` |
| Rust | inline `#[cfg(test)]` | `#[test] fn test_x()` |
| Java | `*Test.java` | `@Test` annotations |

Monorepo: each workspace uses own test framework. Check `.akemi/akemi.yaml` workspaces section for framework.

## Graph Integration

- Every test file MUST have test graph node
- Test node `refs` MUST include `tests` edges to all covered source nodes
- Test-coverage view tracks covered vs uncovered
- Run `/akemi-validate` to find graph coverage gaps

## What Must Be Tested

- All public methods on public classes
- All API endpoint handlers (happy + error)
- All validation logic
- All business rules
- Edge cases: null/undefined, empty collections, boundary values

## What Should Not Be Tested

- Private methods (test via public interface)
- Framework internals
- Third-party lib behavior
- Pure configuration