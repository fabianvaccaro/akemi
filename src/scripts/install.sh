#!/usr/bin/env bash
# Akemi installer - installs the Akemi agent and graph structure into a project.
# Supports local and remote (SSH) installation.
set -euo pipefail

AKEMI_VERSION="0.0.1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKELETON_DIR="$SCRIPT_DIR/../skeleton"

usage() {
  cat << EOF
Akemi v${AKEMI_VERSION} - AI Agent for Graph-Based Codebase Documentation

Usage: akemi install [OPTIONS] [TARGET_PATH]

Options:
  --local              Install in target directory (default)
  --ssh USER@HOST:PATH Install on remote host via SSH
  --skip-bootstrap     Create structure only, don't scan codebase
  --agent AGENT        Agent to configure: claude (default), copilot, codex, gemini, cursor, aider
  --depth DEPTH        Bootstrap depth: tier1, tier2 (default)
  --monorepo           Force monorepo detection (auto-detected by default)
  --dry-run            Show what would be done
  -h, --help           Show this help

Examples:
  $(basename "$0") .                              # Install in current directory
  $(basename "$0") /path/to/project               # Install in specific directory
  $(basename "$0") --ssh user@server:/app          # Remote install via SSH
  $(basename "$0") --skip-bootstrap --agent claude # Structure only
EOF
}

# Defaults
TARGET_MODE="local"
TARGET_PATH="."
SKIP_BOOTSTRAP=false
AGENT="claude"
DEPTH="tier2"
DRY_RUN=false
FORCE_MONOREPO=false
SSH_TARGET=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --local) TARGET_MODE="local"; shift ;;
    --ssh) TARGET_MODE="ssh"; SSH_TARGET="$2"; shift 2 ;;
    --skip-bootstrap) SKIP_BOOTSTRAP=true; shift ;;
    --agent) AGENT="$2"; shift 2 ;;
    --depth) DEPTH="$2"; shift 2 ;;
    --monorepo) FORCE_MONOREPO=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
    *) TARGET_PATH="$1"; shift ;;
  esac
done

# Validate option values: they are interpolated into a remote ssh command,
# so restrict them to the known sets
case "$AGENT" in
  claude|copilot|codex|gemini|cursor|aider) ;;
  *) echo "ERROR: invalid --agent '${AGENT}' (claude|copilot|codex|gemini|cursor|aider)" >&2; exit 1 ;;
esac
case "$DEPTH" in
  tier1|tier2) ;;
  *) echo "ERROR: invalid --depth '${DEPTH}' (tier1|tier2)" >&2; exit 1 ;;
esac

install_local() {
  local project_dir="$1"
  project_dir=$(cd "$project_dir" && pwd)

  echo "==> Installing Akemi v${AKEMI_VERSION} in ${project_dir}"

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "  [DRY RUN] Would create .akemi/ structure"
    echo "  [DRY RUN] Would configure ${AGENT} integration"
    [[ "$SKIP_BOOTSTRAP" == "false" ]] && echo "  [DRY RUN] Would bootstrap graph"
    return 0
  fi

  # Check if already installed
  if [[ -d "$project_dir/.akemi" ]]; then
    echo "  WARNING: .akemi/ already exists. Updating configuration..."
  fi

  # Step 1: Create directory structure
  echo "  Creating .akemi/ structure..."
  mkdir -p "$project_dir/.akemi"/{graph/{nodes/{domain,module,file,class,interface,function,api,resource,requirement,adr,technology,test,doc,config,epic,story,task,bug,capability,feature,pi,iteration,objective},views},guidelines,templates/{node,code},agents/{claude/{rules,skills,commands,agents},cursor,aider,windsurf},scripts,journeys,designs}

  # Step 2: Copy skeleton files
  echo "  Installing skeleton files..."

  # Config
  [[ ! -f "$project_dir/.akemi/akemi.yaml" ]] && \
    cp "$SKELETON_DIR/akemi.yaml" "$project_dir/.akemi/akemi.yaml"

  # Index template
  [[ ! -f "$project_dir/.akemi/graph/index.yaml" ]] && \
    cp "$SKELETON_DIR/graph/index.yaml" "$project_dir/.akemi/graph/index.yaml"

  # View templates
  for view in architecture api-surface test-coverage dependency-tree tech-stack backlog; do
    [[ ! -f "$project_dir/.akemi/graph/views/${view}.md" ]] && \
      cp "$SKELETON_DIR/graph/views/${view}.md" "$project_dir/.akemi/graph/views/${view}.md"
  done

  # Node templates
  for kind in domain module file class interface function api resource requirement adr technology test doc config epic story task bug capability feature pi iteration objective; do
    cp "$SKELETON_DIR/templates/node/${kind}.yaml" "$project_dir/.akemi/templates/node/${kind}.yaml"
  done

  # Guidelines
  for guide in coding-standards testing-standards documentation-standards graph-maintenance ai-friendly safe-scrum; do
    cp "$SKELETON_DIR/guidelines/${guide}.md" "$project_dir/.akemi/guidelines/${guide}.md"
  done

  # Journey schema and template
  cp "$SKELETON_DIR/journeys/SCHEMA.md" "$project_dir/.akemi/journeys/SCHEMA.md"
  cp "$SKELETON_DIR/templates/journey-template.yaml" "$project_dir/.akemi/templates/journey-template.yaml"

  # Scripts (thin wrappers, POSIX and Windows)
  for script in bootstrap rebuild-index rebuild-views validate sync-claude; do
    cp "$SCRIPT_DIR/${script}.sh" "$project_dir/.akemi/scripts/${script}.sh"
    cp "$SCRIPT_DIR/${script}.cmd" "$project_dir/.akemi/scripts/${script}.cmd"
  done
  chmod +x "$project_dir/.akemi/scripts/"*.sh

  # Python package
  echo "  Installing Python modules..."
  local python_src="$SCRIPT_DIR/../python"
  local python_dest="$project_dir/.akemi/python"
  mkdir -p "$python_dest/akemi"
  cp "$python_src/pyproject.toml" "$python_dest/pyproject.toml"
  cp "$python_src/akemi/"*.py "$python_dest/akemi/"

  # Python venv (bin/ on POSIX, Scripts/ when running under Git Bash on Windows)
  local venv_dir="$project_dir/.akemi/.venv"
  local venv_python=""
  find_venv_python() {
    local c
    for c in "$venv_dir/bin/python" "$venv_dir/Scripts/python.exe"; do
      [[ -x "$c" ]] && { echo "$c"; return 0; }
    done
    return 1
  }
  if ! venv_python="$(find_venv_python)"; then
    echo "  Creating Python virtual environment..."
    local boot_python
    boot_python="$(command -v python3 || command -v python || command -v py)" \
      || { echo "ERROR: no Python interpreter found (need python3 >= 3.10)" >&2; exit 1; }
    "$boot_python" -m venv "$venv_dir"
    venv_python="$(find_venv_python)"
    "$venv_python" -m pip install --quiet --upgrade pip
  fi
  echo "  Installing Python dependencies..."
  "$venv_python" -m pip install --quiet "$python_dest/"

  # Step 3: Agent integration
  echo "  Configuring ${AGENT} integration..."

  # Shared graph-first briefing for instruction-file based agents
  # (copilot, codex, gemini). Appends to the target file; skips if the
  # "<!-- akemi -->" marker is already present.
  write_agent_briefing() {
    local target_file="$1"
    if [[ -f "$target_file" ]] && grep -qF "<!-- akemi -->" "$target_file"; then
      echo "  Akemi block already present in ${target_file}"
      return 0
    fi
    mkdir -p "$(dirname "$target_file")"
    cat >> "$target_file" << 'BRIEFING'
<!-- akemi -->
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
BRIEFING
    echo "  Wrote Akemi briefing to ${target_file}"
  }

  case "$AGENT" in
    claude)
      # Copy Claude agent files
      cp "$SKELETON_DIR/agents/claude/CLAUDE.md" "$project_dir/.akemi/agents/claude/CLAUDE.md"

      # Rules
      for rule in "$SKELETON_DIR"/agents/claude/rules/*.md; do
        [[ -f "$rule" && "$rule" != *.original.md ]] && cp "$rule" "$project_dir/.akemi/agents/claude/rules/"
      done

      # Skills
      for skill_dir in "$SKELETON_DIR"/agents/claude/skills/*/; do
        [[ -d "$skill_dir" ]] || continue
        local sname
        sname=$(basename "$skill_dir")
        mkdir -p "$project_dir/.akemi/agents/claude/skills/$sname"
        cp -r "$skill_dir"* "$project_dir/.akemi/agents/claude/skills/$sname/"
        rm -f "$project_dir/.akemi/agents/claude/skills/$sname/"*.original.md
      done

      # Commands
      for cmd in "$SKELETON_DIR"/agents/claude/commands/*.md; do
        [[ -f "$cmd" && "$cmd" != *.original.md ]] && cp "$cmd" "$project_dir/.akemi/agents/claude/commands/"
      done

      # Agents
      for agent_file in "$SKELETON_DIR"/agents/claude/agents/*.md; do
        [[ -f "$agent_file" && "$agent_file" != *.original.md ]] && cp "$agent_file" "$project_dir/.akemi/agents/claude/agents/"
      done

      # Create hooks.json
      cat > "$project_dir/.akemi/agents/claude/hooks.json" << 'HOOKS'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "touch .akemi/.index-stale 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
HOOKS

      # Sync to .claude/ using the project venv just provisioned
      "$venv_python" -m akemi sync-claude "$project_dir"
      ;;
    copilot)
      write_agent_briefing "$project_dir/.github/copilot-instructions.md"
      ;;
    codex)
      write_agent_briefing "$project_dir/AGENTS.md"
      ;;
    gemini)
      write_agent_briefing "$project_dir/GEMINI.md"
      ;;
    cursor)
      echo "  Cursor adapter not yet implemented. Structure created for future use."
      ;;
    aider)
      echo "  Aider adapter not yet implemented. Structure created for future use."
      ;;
    *)
      echo "  WARNING: Unknown agent '${AGENT}'. No integration configured."
      ;;
  esac

  # Step 4: Git configuration
  if [[ -d "$project_dir/.git" ]]; then
    echo "  Configuring git..."
    local gitignore="$project_dir/.gitignore"
    for entry in ".akemi/.index-stale" ".akemi/.venv/" ".akemi/python/*.egg-info/" ".claude/settings.local.json" ".claude/worktrees/"; do
      if [[ ! -f "$gitignore" ]] || ! grep -qF "$entry" "$gitignore"; then
        echo "$entry" >> "$gitignore"
      fi
    done
  fi

  # Step 5: Bootstrap
  if [[ "$SKIP_BOOTSTRAP" == "false" ]]; then
    echo ""
    if [[ "$FORCE_MONOREPO" == "true" ]]; then
      export AKEMI_FORCE_MONOREPO=1
    fi
    "$venv_python" -m akemi bootstrap "$project_dir" "$DEPTH"
  fi

  echo ""
  echo "==> Akemi v${AKEMI_VERSION} installed successfully!"
  echo ""
  echo "    Structure: $project_dir/.akemi/"
  echo "    Agent: ${AGENT}"
  echo ""
  echo "    Quick start:"
  echo "    1. Open Claude Code in this project"
  echo "    2. Run /akemi-status to verify installation"
  echo "    3. Run /akemi-validate to check graph integrity"
}

install_ssh() {
  local ssh_target="$1"
  local ssh_host="${ssh_target%%:*}"
  local remote_path="${ssh_target##*:}"

  echo "==> Installing Akemi v${AKEMI_VERSION} on ${ssh_host}:${remote_path}"

  # Verify SSH access
  if ! ssh -o ConnectTimeout=5 "$ssh_host" "test -d '${remote_path}'" 2>/dev/null; then
    echo "ERROR: Cannot access ${ssh_host}:${remote_path}" >&2
    exit 1
  fi

  # Package and upload
  echo "  Packaging Akemi..."
  local tmpdir
  tmpdir=$(mktemp -d)
  local tarball="$tmpdir/akemi-install.tar.gz"

  tar -czf "$tarball" -C "$(dirname "$SCRIPT_DIR")" scripts skeleton

  echo "  Uploading to ${ssh_host}..."
  ssh "$ssh_host" "mkdir -p /tmp/akemi-install"
  scp -q "$tarball" "${ssh_host}:/tmp/akemi-install/"

  echo "  Running installer remotely..."
  ssh "$ssh_host" "cd '${remote_path}' && \
    tar -xzf /tmp/akemi-install/akemi-install.tar.gz -C /tmp/akemi-install/ && \
    bash /tmp/akemi-install/scripts/install.sh \
      --local --agent ${AGENT} --depth ${DEPTH} \
      ${SKIP_BOOTSTRAP:+--skip-bootstrap} \
      '${remote_path}' && \
    rm -rf /tmp/akemi-install"

  rm -rf "$tmpdir"
  echo "==> Remote installation complete"
}

# Main
case "$TARGET_MODE" in
  local) install_local "$TARGET_PATH" ;;
  ssh) install_ssh "$SSH_TARGET" ;;
esac
