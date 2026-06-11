#!/usr/bin/env bash
# Sync .akemi/agents/claude/ artifacts into .claude/ directory.
# Copies rules, skills, commands, agents, and merges hooks into settings.json.
set -euo pipefail
shopt -s nullglob

PROJECT_ROOT="${1:-.}"
AKEMI_CLAUDE="$PROJECT_ROOT/.akemi/agents/claude"
DOT_CLAUDE="$PROJECT_ROOT/.claude"

if [[ ! -d "$AKEMI_CLAUDE" ]]; then
  echo "ERROR: $AKEMI_CLAUDE not found" >&2
  exit 1
fi

mkdir -p "$DOT_CLAUDE"/{rules,skills,commands,agents}

# Sync rules
synced=0
for rule in "$AKEMI_CLAUDE"/rules/*.md; do
  [[ -f "$rule" ]] || continue
  cp "$rule" "$DOT_CLAUDE/rules/$(basename "$rule")"
  synced=$((synced + 1))
done
echo "  Rules synced: $synced"

# Sync skills (each is a directory with SKILL.md)
synced=0
for skill_dir in "$AKEMI_CLAUDE"/skills/*/; do
  [[ -d "$skill_dir" ]] || continue
  local_name=$(basename "$skill_dir")
  mkdir -p "$DOT_CLAUDE/skills/$local_name"
  cp -r "$skill_dir"* "$DOT_CLAUDE/skills/$local_name/"
  synced=$((synced + 1))
done
echo "  Skills synced: $synced"

# Sync commands
synced=0
for cmd in "$AKEMI_CLAUDE"/commands/*.md; do
  [[ -f "$cmd" ]] || continue
  cp "$cmd" "$DOT_CLAUDE/commands/$(basename "$cmd")"
  synced=$((synced + 1))
done
echo "  Commands synced: $synced"

# Sync agents
synced=0
for agent in "$AKEMI_CLAUDE"/agents/*.md; do
  [[ -f "$agent" ]] || continue
  cp "$agent" "$DOT_CLAUDE/agents/$(basename "$agent")"
  synced=$((synced + 1))
done
echo "  Agents synced: $synced"

# Merge hooks into settings.json
if [[ -f "$AKEMI_CLAUDE/hooks.json" ]]; then
  if command -v jq &>/dev/null; then
    if [[ -f "$DOT_CLAUDE/settings.json" ]]; then
      jq -s '.[0] * .[1]' "$DOT_CLAUDE/settings.json" "$AKEMI_CLAUDE/hooks.json" \
        > "$DOT_CLAUDE/settings.json.tmp" && mv "$DOT_CLAUDE/settings.json.tmp" "$DOT_CLAUDE/settings.json"
    else
      cp "$AKEMI_CLAUDE/hooks.json" "$DOT_CLAUDE/settings.json"
    fi
    echo "  Hooks merged into settings.json"
  else
    echo "  WARNING: jq not found, skipping hooks merge"
  fi
fi

# Ensure root CLAUDE.md has the @import
CLAUDE_MD="$PROJECT_ROOT/CLAUDE.md"
IMPORT_LINE="@.akemi/agents/claude/CLAUDE.md"

if [[ ! -f "$CLAUDE_MD" ]]; then
  echo "$IMPORT_LINE" > "$CLAUDE_MD"
  echo "  Created CLAUDE.md with Akemi import"
elif ! grep -qF "$IMPORT_LINE" "$CLAUDE_MD"; then
  # Prepend import to existing CLAUDE.md
  tmp=$(mktemp)
  echo "$IMPORT_LINE" > "$tmp"
  echo "" >> "$tmp"
  cat "$CLAUDE_MD" >> "$tmp"
  mv "$tmp" "$CLAUDE_MD"
  echo "  Added Akemi import to existing CLAUDE.md"
else
  echo "  CLAUDE.md already has Akemi import"
fi

echo "Claude sync complete."
