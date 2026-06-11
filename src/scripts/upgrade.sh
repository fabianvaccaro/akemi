#!/usr/bin/env bash
# Upgrade an existing Akemi installation to the latest version.
# Safe: only adds new files and updates templates/agents/scripts.
# Never deletes or modifies existing graph nodes.
set -euo pipefail

AKEMI_VERSION="0.3.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKELETON_DIR="$SCRIPT_DIR/../skeleton"

PROJECT_ROOT="${1:-.}"
PROJECT_ROOT=$(cd "$PROJECT_ROOT" && pwd)
AKEMI_DIR="$PROJECT_ROOT/.akemi"

if [[ ! -d "$AKEMI_DIR" ]]; then
  echo "ERROR: $AKEMI_DIR not found. Run install first." >&2
  exit 1
fi

echo "==> Upgrading Akemi to v${AKEMI_VERSION} in ${PROJECT_ROOT}"

# Step 1: Create new directories (safe - mkdir -p won't touch existing)
echo "  Adding new directories..."
for kind in epic story task bug capability feature pi iteration objective; do
  mkdir -p "$AKEMI_DIR/graph/nodes/$kind"
done
mkdir -p "$AKEMI_DIR/journeys"
mkdir -p "$AKEMI_DIR/designs"

# Step 2: Copy new templates (safe - only adds, doesn't overwrite existing node files)
echo "  Updating node templates..."
for kind in domain module file class interface function api resource requirement adr technology test doc config epic story task bug capability feature pi iteration objective; do
  cp "$SKELETON_DIR/templates/node/${kind}.yaml" "$AKEMI_DIR/templates/node/${kind}.yaml" 2>/dev/null || true
done

# Step 3: Update scripts (safe - replaces scripts, not data)
echo "  Updating scripts..."
cp "$SCRIPT_DIR/rebuild-index.sh" "$AKEMI_DIR/scripts/rebuild-index.sh"
cp "$SCRIPT_DIR/rebuild-views.sh" "$AKEMI_DIR/scripts/rebuild-views.sh"
cp "$SCRIPT_DIR/validate.sh" "$AKEMI_DIR/scripts/validate.sh"
cp "$SCRIPT_DIR/sync-claude.sh" "$AKEMI_DIR/scripts/sync-claude.sh"
cp "$SCRIPT_DIR/bootstrap.sh" "$AKEMI_DIR/scripts/bootstrap.sh"
cp "$SCRIPT_DIR/upgrade.sh" "$AKEMI_DIR/scripts/upgrade.sh"
# Legacy bash lib/ removed in 0.2.x: all logic lives in the Python package
rm -rf "$AKEMI_DIR/scripts/lib"
chmod +x "$AKEMI_DIR/scripts/"*.sh

# Step 3b: Update Python package
echo "  Updating Python modules..."
PYTHON_SRC="$SCRIPT_DIR/../python"
PYTHON_DEST="$AKEMI_DIR/python"
mkdir -p "$PYTHON_DEST/akemi"
cp "$PYTHON_SRC/pyproject.toml" "$PYTHON_DEST/pyproject.toml"
cp "$PYTHON_SRC/akemi/"*.py "$PYTHON_DEST/akemi/"

# Ensure venv exists and deps are current
VENV_DIR="$AKEMI_DIR/.venv"
if [[ ! -f "$VENV_DIR/bin/python" ]]; then
  echo "  Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
fi
echo "  Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade "$PYTHON_DEST/"

# Add venv to gitignore if not already
if [[ -d "$PROJECT_ROOT/.git" ]]; then
  GITIGNORE="$PROJECT_ROOT/.gitignore"
  for entry in ".akemi/.venv/" ".akemi/python/*.egg-info/"; do
    if [[ ! -f "$GITIGNORE" ]] || ! grep -qF "$entry" "$GITIGNORE"; then
      echo "$entry" >> "$GITIGNORE"
    fi
  done
fi

# Step 3c: Update journey schema and template
echo "  Updating journey schema and template..."
cp "$SKELETON_DIR/journeys/SCHEMA.md" "$AKEMI_DIR/journeys/SCHEMA.md"
cp "$SKELETON_DIR/templates/journey-template.yaml" "$AKEMI_DIR/templates/journey-template.yaml"

# Step 4: Update guidelines (safe - overwrites guidelines, not user content)
echo "  Updating guidelines..."
for guide in coding-standards testing-standards documentation-standards graph-maintenance ai-friendly safe-scrum; do
  cp "$SKELETON_DIR/guidelines/${guide}.md" "$AKEMI_DIR/guidelines/${guide}.md"
done

# Step 5: Update Claude agent files (safe - overwrites agent definitions)
echo "  Updating Claude integration..."
cp "$SKELETON_DIR/agents/claude/CLAUDE.md" "$AKEMI_DIR/agents/claude/CLAUDE.md"

for rule in "$SKELETON_DIR"/agents/claude/rules/*.md; do
  [[ -f "$rule" && "$rule" != *.original.md ]] && cp "$rule" "$AKEMI_DIR/agents/claude/rules/"
done

for skill_dir in "$SKELETON_DIR"/agents/claude/skills/*/; do
  [[ -d "$skill_dir" ]] || continue
  sname=$(basename "$skill_dir")
  mkdir -p "$AKEMI_DIR/agents/claude/skills/$sname"
  cp -r "$skill_dir"* "$AKEMI_DIR/agents/claude/skills/$sname/"
  rm -f "$AKEMI_DIR/agents/claude/skills/$sname/"*.original.md
done

for cmd in "$SKELETON_DIR"/agents/claude/commands/*.md; do
  [[ -f "$cmd" && "$cmd" != *.original.md ]] && cp "$cmd" "$AKEMI_DIR/agents/claude/commands/"
done

for agent in "$SKELETON_DIR"/agents/claude/agents/*.md; do
  [[ -f "$agent" && "$agent" != *.original.md ]] && cp "$agent" "$AKEMI_DIR/agents/claude/agents/"
done

# Step 6: Sync to .claude/ directory
echo "  Syncing to .claude/..."
bash "$SCRIPT_DIR/sync-claude.sh" "$PROJECT_ROOT"

# Step 7: Update akemi.yaml with new prefixes (additive only)
echo "  Updating config..."
AKEMI_YAML="$AKEMI_DIR/akemi.yaml"
if [[ -f "$AKEMI_YAML" ]]; then
  for prefix_line in "    epic: epic" "    story: story" "    task: task" "    bug: bug" "    capability: cap" "    feature: feat" "    pi: pi" "    iteration: iter" "    objective: obj"; do
    if ! grep -qF "$prefix_line" "$AKEMI_YAML"; then
      # Add after the config prefix line
      sed -i.bak "/    config: cfg/a\\
${prefix_line}" "$AKEMI_YAML"
    fi
  done
  rm -f "$AKEMI_YAML.bak"
fi

# Step 8: Add project type field if missing
if [[ -f "$AKEMI_YAML" ]] && ! grep -q '^  type:' "$AKEMI_YAML"; then
  echo "  Adding project type field..."
  sed -i.bak '/^  name:/a\
  type: single' "$AKEMI_YAML"
  rm -f "$AKEMI_YAML.bak"
fi

# Step 9: Rebuild index to recognize new kinds
echo "  Rebuilding index..."
bash "$SCRIPT_DIR/rebuild-index.sh" "$AKEMI_DIR"

echo "  Rebuilding views..."
bash "$SCRIPT_DIR/rebuild-views.sh" "$AKEMI_DIR"

echo ""
echo "==> Upgrade to v${AKEMI_VERSION} complete!"
echo "    New: SAFe work item kinds (capability, feature, pi, iteration, objective)"
echo "    New: backlog view and safe-scrum guideline"
echo "    New: Java and Scala support (Maven, Gradle, sbt)"
echo "    Updated: agent definitions with graph-first workflow and failure protocol"
echo "    Existing graph nodes: untouched"
