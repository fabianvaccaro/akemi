# Contributing to Akemi

Thanks for your interest in improving Akemi. This document defines the
conventions used across the project: repository structure, naming, commits,
versioning, and releases.

## Repository structure

```
akemi/
  LICENSE             # MIT, applies to the whole repository
  README.md           # user documentation
  CHANGELOG.md        # release history, Keep a Changelog format
  CONTRIBUTING.md     # this file
  package.json        # npm metadata for the installer entry point
  src/
    python/           # the akemi Python package (PyYAML is the only runtime dep)
    scripts/          # installers and thin wrappers (.sh for POSIX, .cmd for Windows)
    skeleton/         # files copied into target projects under .akemi/
```

## Design principles

1. Plain text first: the graph is YAML files in the repository, never a
   database or a server.
2. Minimal dependencies: PyYAML is the only required runtime dependency.
   Optional features go behind extras (for example `parsers` for
   tree-sitter).
3. Cross-platform: every feature must work on Windows, macOS, and Linux.
   New logic goes in the Python package, never in bash only. Shell and
   batch wrappers stay thin.
4. License compliance: the project is MIT. Every dependency, vendored
   snippet, or copied file must carry a permissive license (MIT, BSD,
   Apache-2.0, ISC). Copyleft licenses (GPL, AGPL, LGPL, MPL, CC-BY-SA)
   are not accepted in any form.

## Branch naming

- `main` is the release branch and must always be installable.
- Work branches use a type prefix and a short kebab-case slug:
  - `feat/<slug>` for new functionality
  - `fix/<slug>` for bug fixes
  - `docs/<slug>` for documentation only
  - `chore/<slug>` for maintenance, tooling, and dependencies
  - `release/<version>` for release preparation

## Commit convention

Commits follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```
<type>: <subject>

<optional body>
```

- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `build`,
  `release`.
- Subject: imperative mood, lower case after the type, no trailing period,
  72 characters or less.
- Body: plain direct language explaining what changed and why. Wrap at 72
  characters. Skip the body when the subject says it all.
- Breaking changes: add a `!` after the type (`feat!:`) and explain the
  break in the body.
- Do not use em-dashes anywhere in commit messages or documentation.

Examples:

```
feat: add Windows support with portable installer and cmd wrappers
fix: detect Scripts layout when creating the venv under Git Bash
docs: document the sync-claude subcommand
release: 0.0.1
```

## Versioning convention

Akemi follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

- Pre-1.0 (`0.y.z`): `y` increments for new features or behavior changes,
  `z` increments for fixes and documentation. Anything may change between
  `0.y` versions.
- From 1.0.0 on: `major.minor.patch` with the standard SemVer contract.

The version lives in these files and they must always agree:

- `src/python/pyproject.toml` (`version`)
- `src/python/akemi/__init__.py` (`__version__`)
- `src/scripts/install.sh` (`AKEMI_VERSION`)
- `src/scripts/upgrade.sh` (`AKEMI_VERSION`)
- `src/scripts/install.py` (`AKEMI_VERSION`)
- `package.json` (`version`)

## Release convention

Releases are cut from `main` and named `Akemi <version>`. Git tags use a
`v` prefix: `v0.0.1`.

Checklist for every release:

1. All version files above bumped to the new version and in agreement.
2. `CHANGELOG.md` has a dated section for the version with Added, Changed,
   Fixed, and Removed subsections as needed.
3. Fresh install verified on a throwaway project: `install.sh` on POSIX,
   `install.py` on Windows or with the system Python.
4. `validate`, `rebuild-index`, and `rebuild-views` run clean on the
   throwaway project.
5. No tracked build artifacts (`build/`, `dist/`, `*.egg-info`, `.venv`),
   no secrets, no personal information in the tree.
6. Commit `release: <version>`, tag `v<version>` (annotated), push the
   branch and the tag.
7. Pushing the tag triggers the `release` workflow
   (`.github/workflows/release.yml`). It checks that every version file
   agrees with the tag, extracts the changelog section, and creates the
   GitHub release. Verify the release appears under the Releases tab; if
   the workflow fails, fix the cause and re-run it from the Actions tab.

## Code style

- Python: standard library plus PyYAML only. Type hints on public
  functions. Explicit `encoding="utf-8"` on every file read and write.
  Paths through `pathlib`; node IDs always use forward slashes.
- Shell: `bash` with `set -euo pipefail`. Keep wrappers thin and delegate
  to `python -m akemi`.
- Batch: mirror the matching `.sh` wrapper. CRLF line endings, enforced by
  `.gitattributes`.
- Markdown: plain direct language. No em-dashes.
