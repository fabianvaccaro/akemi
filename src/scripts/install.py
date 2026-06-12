#!/usr/bin/env python3
"""Akemi installer - installs the Akemi agent and graph structure into a project.

Cross-platform (Windows, macOS, Linux), Python stdlib only. For remote SSH
installation use install.sh on a POSIX host.

Usage: python install.py [OPTIONS] [TARGET_PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

AKEMI_VERSION = "0.1.0"

SCRIPT_DIR = Path(__file__).resolve().parent
SKELETON_DIR = SCRIPT_DIR.parent / "skeleton"
PYTHON_SRC = SCRIPT_DIR.parent / "python"

NODE_KINDS = [
    "domain", "module", "file", "class", "interface", "function", "api",
    "resource", "requirement", "adr", "technology", "test", "doc", "config",
    "epic", "story", "task", "bug", "capability", "feature", "pi",
    "iteration", "objective",
]
VIEWS = ["architecture", "api-surface", "test-coverage", "dependency-tree",
         "tech-stack", "backlog"]
GUIDELINES = ["coding-standards", "testing-standards", "documentation-standards",
              "graph-maintenance", "ai-friendly", "safe-scrum"]
SHELL_SCRIPTS = ["bootstrap", "rebuild-index", "rebuild-views", "validate",
                 "sync-claude"]
AGENTS = ["claude", "copilot", "codex", "gemini", "cursor", "aider"]

BRIEFING = """<!-- akemi -->
## Akemi codebase graph

This project documents its codebase as a YAML graph under `.akemi/`.

Before making changes:
- Read `.akemi/graph/index.yaml` to locate the nodes relevant to the task.
- Open the node files it points to under `.akemi/graph/nodes/<kind>/`.

After making changes:
- Update the YAML node for each file, class, or function you changed.
- Add new nodes from `.akemi/templates/node/` when you create new code.
- Run `.akemi/scripts/validate.sh` and fix anything it reports.

Key node kinds: domain, module, file, class, interface, function, api, test, adr.
Work items: epic > capability > feature > story (plus task and bug).
Generated views live in `.akemi/graph/views/`. Do not edit them by hand;
regenerate with `.akemi/scripts/rebuild-views.sh`.
<!-- /akemi -->
"""


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def hook_touch_command() -> str:
    """Command that marks the index stale; must work in the platform shell."""
    if os.name == "nt":
        # Works from cmd, PowerShell, and Git Bash alike.
        return 'cmd /c "type nul > .akemi\\.index-stale"'
    return "touch .akemi/.index-stale 2>/dev/null || true"


def copy_if_missing(src: Path, dest: Path) -> None:
    if not dest.exists():
        shutil.copy2(src, dest)


def write_agent_briefing(target_file: Path) -> None:
    """Append the graph-first briefing once, guarded by the akemi marker."""
    if target_file.is_file() and "<!-- akemi -->" in target_file.read_text(encoding="utf-8"):
        print(f"  Akemi block already present in {target_file}")
        return
    target_file.parent.mkdir(parents=True, exist_ok=True)
    with target_file.open("a", encoding="utf-8") as fh:
        fh.write(BRIEFING)
    print(f"  Wrote Akemi briefing to {target_file}")


def run(cmd: list[str], env: dict | None = None) -> None:
    subprocess.run(cmd, check=True, env=env)


def install_local(project_dir: Path, agent: str, depth: str,
                  skip_bootstrap: bool, force_monorepo: bool,
                  dry_run: bool) -> None:
    project_dir = project_dir.resolve()
    print(f"==> Installing Akemi v{AKEMI_VERSION} in {project_dir}")

    if dry_run:
        print("  [DRY RUN] Would create .akemi/ structure")
        print(f"  [DRY RUN] Would configure {agent} integration")
        if not skip_bootstrap:
            print("  [DRY RUN] Would bootstrap graph")
        return

    akemi_dir = project_dir / ".akemi"
    if akemi_dir.is_dir():
        print("  WARNING: .akemi/ already exists. Updating configuration...")

    # Step 1: Create directory structure
    print("  Creating .akemi/ structure...")
    for kind in NODE_KINDS:
        (akemi_dir / "graph" / "nodes" / kind).mkdir(parents=True, exist_ok=True)
    for sub in ("graph/views", "guidelines", "templates/node", "templates/code",
                "agents/claude/rules", "agents/claude/skills",
                "agents/claude/commands", "agents/claude/agents",
                "agents/cursor", "agents/aider", "agents/windsurf",
                "scripts", "journeys", "designs"):
        (akemi_dir / Path(sub)).mkdir(parents=True, exist_ok=True)

    # Step 2: Copy skeleton files
    print("  Installing skeleton files...")
    copy_if_missing(SKELETON_DIR / "akemi.yaml", akemi_dir / "akemi.yaml")
    copy_if_missing(SKELETON_DIR / "graph" / "index.yaml",
                    akemi_dir / "graph" / "index.yaml")
    for view in VIEWS:
        copy_if_missing(SKELETON_DIR / "graph" / "views" / f"{view}.md",
                        akemi_dir / "graph" / "views" / f"{view}.md")
    for kind in NODE_KINDS:
        shutil.copy2(SKELETON_DIR / "templates" / "node" / f"{kind}.yaml",
                     akemi_dir / "templates" / "node" / f"{kind}.yaml")
    for guide in GUIDELINES:
        shutil.copy2(SKELETON_DIR / "guidelines" / f"{guide}.md",
                     akemi_dir / "guidelines" / f"{guide}.md")
    shutil.copy2(SKELETON_DIR / "journeys" / "SCHEMA.md",
                 akemi_dir / "journeys" / "SCHEMA.md")
    shutil.copy2(SKELETON_DIR / "templates" / "journey-template.yaml",
                 akemi_dir / "templates" / "journey-template.yaml")

    # Scripts (thin wrappers, POSIX and Windows)
    for name in SHELL_SCRIPTS:
        for ext in (".sh", ".cmd"):
            src = SCRIPT_DIR / f"{name}{ext}"
            if src.is_file():
                dest = akemi_dir / "scripts" / src.name
                shutil.copy2(src, dest)
                if ext == ".sh" and os.name != "nt":
                    dest.chmod(dest.stat().st_mode | 0o755)

    # Python package
    print("  Installing Python modules...")
    python_dest = akemi_dir / "python"
    (python_dest / "akemi").mkdir(parents=True, exist_ok=True)
    shutil.copy2(PYTHON_SRC / "pyproject.toml", python_dest / "pyproject.toml")
    for py in (PYTHON_SRC / "akemi").glob("*.py"):
        shutil.copy2(py, python_dest / "akemi" / py.name)

    # Python venv
    venv_dir = akemi_dir / ".venv"
    py = venv_python(venv_dir)
    if not py.is_file():
        print("  Creating Python virtual environment...")
        run([sys.executable, "-m", "venv", str(venv_dir)])
        run([str(py), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    print("  Installing Python dependencies...")
    run([str(py), "-m", "pip", "install", "--quiet", str(python_dest)])

    # Step 3: Agent integration
    print(f"  Configuring {agent} integration...")
    if agent == "claude":
        claude_skel = SKELETON_DIR / "agents" / "claude"
        claude_dest = akemi_dir / "agents" / "claude"
        shutil.copy2(claude_skel / "CLAUDE.md", claude_dest / "CLAUDE.md")
        for sub in ("rules", "commands", "agents"):
            for f in (claude_skel / sub).glob("*.md"):
                if not f.name.endswith(".original.md"):
                    shutil.copy2(f, claude_dest / sub / f.name)
        for skill_dir in (claude_skel / "skills").iterdir():
            if not skill_dir.is_dir():
                continue
            target = claude_dest / "skills" / skill_dir.name
            shutil.copytree(skill_dir, target, dirs_exist_ok=True)
            for orig in target.rglob("*.original.md"):
                orig.unlink()

        hooks = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Edit|Write",
                        "hooks": [
                            {"type": "command", "command": hook_touch_command()}
                        ],
                    }
                ]
            }
        }
        (claude_dest / "hooks.json").write_text(
            json.dumps(hooks, indent=2) + "\n", encoding="utf-8"
        )

        run([str(py), "-m", "akemi", "sync-claude", str(project_dir)])
    elif agent == "copilot":
        write_agent_briefing(project_dir / ".github" / "copilot-instructions.md")
    elif agent == "codex":
        write_agent_briefing(project_dir / "AGENTS.md")
    elif agent == "gemini":
        write_agent_briefing(project_dir / "GEMINI.md")
    else:
        print(f"  {agent.capitalize()} adapter not yet implemented. "
              "Structure created for future use.")

    # Step 4: Git configuration
    if (project_dir / ".git").is_dir():
        print("  Configuring git...")
        gitignore = project_dir / ".gitignore"
        existing = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
        additions = [e for e in (".akemi/.index-stale", ".akemi/.venv/",
                                 ".akemi/python/*.egg-info/",
                                 ".claude/settings.local.json",
                                 ".claude/worktrees/")
                     if e not in existing]
        if additions:
            if existing and not existing.endswith("\n"):
                existing += "\n"
            gitignore.write_text(existing + "\n".join(additions) + "\n",
                                 encoding="utf-8")

    # Step 5: Bootstrap
    if not skip_bootstrap:
        print("")
        env = os.environ.copy()
        if force_monorepo:
            env["AKEMI_FORCE_MONOREPO"] = "1"
        run([str(py), "-m", "akemi", "bootstrap", str(project_dir), depth],
            env=env)

    print(f"""
==> Akemi v{AKEMI_VERSION} installed successfully!

    Structure: {akemi_dir}
    Agent: {agent}

    Quick start:
    1. Open Claude Code in this project
    2. Run /akemi-status to verify installation
    3. Run /akemi-validate to check graph integrity""")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="install.py",
        description=f"Akemi v{AKEMI_VERSION} - AI Agent for Graph-Based "
                    "Codebase Documentation",
    )
    parser.add_argument("target_path", nargs="?", default=".",
                        help="Target project directory (default: .)")
    parser.add_argument("--skip-bootstrap", action="store_true",
                        help="Create structure only, don't scan codebase")
    parser.add_argument("--agent", default="claude", choices=AGENTS,
                        help="Agent to configure (default: claude)")
    parser.add_argument("--depth", default="tier2", choices=["tier1", "tier2"],
                        help="Bootstrap depth (default: tier2)")
    parser.add_argument("--monorepo", action="store_true",
                        help="Force monorepo detection")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done")
    args = parser.parse_args(argv)

    if sys.version_info < (3, 10):
        sys.exit("ERROR: Akemi requires Python 3.10 or newer")
    if not SKELETON_DIR.is_dir() or not PYTHON_SRC.is_dir():
        sys.exit("ERROR: skeleton/ or python/ not found next to scripts/; "
                 "run from a full Akemi checkout")

    target = Path(args.target_path)
    if not target.is_dir():
        sys.exit(f"ERROR: target directory not found: {target}")

    try:
        install_local(target, args.agent, args.depth, args.skip_bootstrap,
                      args.monorepo, args.dry_run)
    except subprocess.CalledProcessError as exc:
        sys.exit(f"ERROR: command failed with exit code {exc.returncode}: "
                 f"{' '.join(exc.cmd)}")


if __name__ == "__main__":
    main()
