---
globs: "{src,app,lib,backend,frontend,server,api,services,scripts}/**/*"
---
# Akemi Development Standards

When creating or modifying source code:

1. Read the graph first: look up the file's node and its edges in `.akemi/graph/index.yaml` before editing
2. Max 300 lines per source file. Split at 250 (use Akemi-Refactorer)
3. Every public class has an interface and is wired via constructor DI (no `new` for internal deps)
4. Naming: files kebab-case, classes PascalCase. Functions follow the workspace language: camelCase (TS/JS, Java, Scala), snake_case (Python, Rust)
5. Monorepo: apply the owning workspace's language and test framework from `.akemi/akemi.yaml` `workspaces:`, not root defaults
6. No bare `index.*`, `utils.*`, `helpers.*` files: use descriptive names
7. Every public class/function has a unit test. Coverage target 90%+
8. Organize by feature/domain (vertical slices), not by layer
9. Work belongs to a task or story node; if none exists, route to Akemi-Planner
10. After any change: create/update the matching node YAML in `.akemi/graph/nodes/`, then run `bash .akemi/scripts/rebuild-index.sh` and `bash .akemi/scripts/validate.sh`
