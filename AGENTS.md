# Akemi agent guide

This repository is the Akemi source tree: graph-based codebase documentation for AI coding agents. If a user asks you to install Akemi into one of their projects, follow the installation procedure below exactly. If you are working on the Akemi source itself, read "Working on this repository" at the end.

## Installing Akemi into a target project

A typical request looks like "install Akemi into /path/to/project and set it up for Claude Code, Copilot, and Gemini". The installer configures one agent integration per run, so the procedure is: one full install for the first agent, then one quick re-run per additional agent.

### 1. Check prerequisites

- Python 3.10 or newer on PATH. Check with `python3 --version` (POSIX) or `python --version` (Windows).
- The target path exists and is a directory.
- If the target is not a git repository, the install still works but the .gitignore step is skipped. Mention this to the user.

### 2. Run the full install for the first agent

Run from the root of this repository. Use `--agent claude` unless the user asked for a different primary agent.

POSIX (macOS, Linux, Git Bash):

```bash
./src/scripts/install.sh --agent claude /path/to/project
```

Windows (PowerShell or cmd):

```powershell
python src\scripts\install.py --agent claude C:\path\to\project
```

`install.py` also works on macOS and Linux (`python3 src/scripts/install.py ...`). This run creates `.akemi/` in the target, builds a private venv at `.akemi/.venv`, configures the agent integration, and bootstraps the graph by scanning the codebase. The scan is the slow part; it runs only once.

### 3. Add the remaining agent integrations

Re-run the installer once per additional agent with `--skip-bootstrap` so the codebase is not rescanned:

```bash
python3 src/scripts/install.py --skip-bootstrap --agent copilot /path/to/project
python3 src/scripts/install.py --skip-bootstrap --agent gemini /path/to/project
python3 src/scripts/install.py --skip-bootstrap --agent codex /path/to/project
```

What each `--agent` value configures in the target project:

| Agent | What the run writes |
|---|---|
| claude | `.akemi/agents/claude/` (rules, skills, commands, subagents) synced into `.claude/`, hooks merged into `.claude/settings.json`, one import line added to `CLAUDE.md` |
| copilot | Akemi instruction block in `.github/copilot-instructions.md` |
| codex | Akemi instruction block appended to `AGENTS.md` in the target project root |
| gemini | Akemi instruction block appended to `GEMINI.md` in the target project root |
| cursor, aider | Directory structure only; the adapter is not implemented yet. Tell the user. |

Re-running is safe. Skeleton files are only copied when missing, instruction blocks are guarded by an `<!-- akemi -->` marker so they are never duplicated, and the venv is reused.

### 4. Verify the installation

- `.akemi/` exists in the target with `akemi.yaml`, `graph/index.yaml`, `graph/nodes/`, `graph/views/`, `guidelines/`, `scripts/`, and `python/`.
- Run the target's validator and confirm it reports zero errors:

```bash
bash /path/to/project/.akemi/scripts/validate.sh
```

On Windows: `C:\path\to\project\.akemi\scripts\validate.cmd`.

- For each agent the user requested, confirm the files in the table above exist.

### 5. Report back

Tell the user: where Akemi was installed, which agent integrations were configured, the validator result, and the daily commands (`.akemi/scripts/validate.sh`, `heal.sh` for mechanical fixes, `rebuild-index.sh`, `rebuild-views.sh`, and `bootstrap.sh` for full rescans).

### Options reference

Both installers accept: `--skip-bootstrap`, `--agent NAME`, `--depth tier1|tier2` (default tier2), `--monorepo`, `--dry-run`, and a target path. `install.sh` additionally supports `--ssh USER@HOST:PATH` for remote installs (POSIX only).

### Troubleshooting

- "skeleton/ or python/ not found": the installer must run from a full Akemi checkout. Do not copy `install.py` out of the repository.
- "Akemi requires Python 3.10 or newer": ask the user to install a newer Python and re-run.
- On Windows, prefer `install.py`. The `.sh` wrappers require Git Bash.
- If a run fails partway, fix the cause and re-run the same command. Completed steps are skipped or harmlessly repeated.

## Working on this repository

- License compliance is a hard requirement. Only permissively licensed dependencies are allowed (MIT, BSD, Apache 2.0, ISC). No copyleft code may be added, linked, or vendored. PyYAML is the only required runtime dependency; keep it that way.
- The trunk stays plain text: YAML graph, no database, no embeddings, no server.
- Cross-platform rules: new logic goes in the Python package (`src/python/akemi/`), never in bash only. Shell wrappers ship in `.sh` and `.cmd` pairs. All file I/O uses explicit UTF-8.
- Branch naming, commit conventions, versioning, and the release process are in [CONTRIBUTING.md](CONTRIBUTING.md).
