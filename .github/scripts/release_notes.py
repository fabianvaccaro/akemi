"""Release helper for the tag-triggered workflow.

Checks that every version file agrees with the version given as the first
argument, then prints the matching CHANGELOG.md section to stdout so the
workflow can use it as the release notes. Exits non-zero on any mismatch.
Standard library only.
"""

import re
import sys
from pathlib import Path

VERSION_FILES = {
    "src/python/pyproject.toml": r'^version = "(?P<v>[^"]+)"',
    "src/python/akemi/__init__.py": r'^__version__ = "(?P<v>[^"]+)"',
    "src/scripts/install.sh": r'^AKEMI_VERSION="(?P<v>[^"]+)"',
    "src/scripts/upgrade.sh": r'^AKEMI_VERSION="(?P<v>[^"]+)"',
    "src/scripts/install.py": r'^AKEMI_VERSION = "(?P<v>[^"]+)"',
    "package.json": r'^  "version": "(?P<v>[^"]+)",',
}


def file_version(path: str, pattern: str) -> str:
    text = Path(path).read_text(encoding="utf-8")
    match = re.search(pattern, text, re.MULTILINE)
    if match is None:
        sys.exit(f"error: no version string found in {path}")
    return match.group("v")


def changelog_section(version: str) -> str:
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith(f"## [{version}]"):
            start = i + 1
            break
    if start is None:
        sys.exit(f"error: CHANGELOG.md has no section for {version}")
    body = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    section = "\n".join(body).strip()
    if not section:
        sys.exit(f"error: CHANGELOG.md section for {version} is empty")
    return section


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: release_notes.py <version>")
    version = sys.argv[1]
    errors = []
    for path, pattern in VERSION_FILES.items():
        found = file_version(path, pattern)
        if found != version:
            errors.append(f"{path}: {found} (expected {version})")
    if errors:
        sys.exit("error: version files disagree with the tag:\n" + "\n".join(errors))
    print(changelog_section(version))


if __name__ == "__main__":
    main()
