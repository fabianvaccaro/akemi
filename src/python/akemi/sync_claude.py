"""Sync .akemi/agents/claude/ artifacts into the project's .claude/ directory.

Copies rules, skills, commands, and agents, merges hooks.json into
.claude/settings.json, and ensures the root CLAUDE.md imports the Akemi
briefing. Pure stdlib, works on POSIX and Windows.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path


def _is_original(path: Path) -> bool:
    return path.name.endswith(".original.md")


def _sync_markdown_files(src_dir: Path, dest_dir: Path) -> int:
    """Copy *.md files (except *.original.md) from src_dir to dest_dir."""
    count = 0
    if not src_dir.is_dir():
        return count
    for f in sorted(src_dir.glob("*.md")):
        if _is_original(f):
            continue
        shutil.copy2(f, dest_dir / f.name)
        count += 1
    return count


def _sync_skills(src_dir: Path, dest_dir: Path) -> int:
    """Copy each skill directory, dropping *.original.md files."""
    count = 0
    if not src_dir.is_dir():
        return count
    for skill_dir in sorted(src_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        target = dest_dir / skill_dir.name
        shutil.copytree(skill_dir, target, dirs_exist_ok=True)
        for orig in target.rglob("*.original.md"):
            orig.unlink()
        count += 1
    return count


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursive dict merge; override wins, arrays are replaced.

    Mirrors jq's '.[0] * .[1]' semantics used by the legacy bash script.
    """
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _merge_hooks(hooks_file: Path, settings_file: Path) -> None:
    hooks = json.loads(hooks_file.read_text(encoding="utf-8"))
    if settings_file.is_file():
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        merged = _deep_merge(settings, hooks)
    else:
        merged = hooks
    settings_file.write_text(
        json.dumps(merged, indent=2) + "\n", encoding="utf-8"
    )


IMPORT_LINE = "@.akemi/agents/claude/CLAUDE.md"


def _ensure_claude_md_import(project_root: Path) -> str:
    claude_md = project_root / "CLAUDE.md"
    if not claude_md.is_file():
        claude_md.write_text(IMPORT_LINE + "\n", encoding="utf-8")
        return "  Created CLAUDE.md with Akemi import"
    content = claude_md.read_text(encoding="utf-8")
    if IMPORT_LINE in content:
        return "  CLAUDE.md already has Akemi import"
    claude_md.write_text(IMPORT_LINE + "\n\n" + content, encoding="utf-8")
    return "  Added Akemi import to existing CLAUDE.md"


def sync_claude(project_root: str = ".") -> str:
    """Sync Akemi Claude artifacts into .claude/. Returns a report string."""
    root = Path(project_root).resolve()
    akemi_claude = root / ".akemi" / "agents" / "claude"
    dot_claude = root / ".claude"

    if not akemi_claude.is_dir():
        raise FileNotFoundError(f"{akemi_claude} not found")

    lines: list[str] = []
    for sub in ("rules", "skills", "commands", "agents"):
        (dot_claude / sub).mkdir(parents=True, exist_ok=True)

    lines.append(
        f"  Rules synced: {_sync_markdown_files(akemi_claude / 'rules', dot_claude / 'rules')}"
    )
    lines.append(
        f"  Skills synced: {_sync_skills(akemi_claude / 'skills', dot_claude / 'skills')}"
    )
    lines.append(
        f"  Commands synced: {_sync_markdown_files(akemi_claude / 'commands', dot_claude / 'commands')}"
    )
    lines.append(
        f"  Agents synced: {_sync_markdown_files(akemi_claude / 'agents', dot_claude / 'agents')}"
    )

    hooks_file = akemi_claude / "hooks.json"
    if hooks_file.is_file():
        _merge_hooks(hooks_file, dot_claude / "settings.json")
        lines.append("  Hooks merged into settings.json")

    lines.append(_ensure_claude_md_import(root))
    lines.append("Claude sync complete.")
    return "\n".join(lines)
