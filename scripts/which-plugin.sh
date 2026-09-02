#!/usr/bin/env bash
set -euo pipefail

# Answers "which repo owns this skill, and what ships it?" — the question every meta skill
# has to get right now that the skills live in two repos and two plugins.
#
# Prints shell-assignable lines: repo, skill_md, plugin, marketplace, update.
# Exits 1 if the skill is in neither repo, 2 if it is somehow in both.
#
# Usage: scripts/which-plugin.sh <skill-name>
#        eval "$(scripts/which-plugin.sh plan-change)" && echo "$update"

skill="${1:-}"
if [ -z "$skill" ]; then
  echo "usage: $(basename "$0") <skill-name>" >&2
  exit 1
fi

# Every repo that ships skills. Both are overridable so a clone anywhere still works.
repos=(
  "${JANKOLENKO_SKILLS_REPO:-$HOME/Developer/skills}"
  "${JANKOLENKO_PROJECTS_REPO:-$HOME/Developer/ai-jankolenko-skills}"
)

found_repo=""
found_md=""
for repo in "${repos[@]}"; do
  [ -d "$repo" ] || continue
  # skills/<bucket>/<skill>/SKILL.md — one bucket level, never two.
  md="$(find "$repo/skills" -mindepth 3 -maxdepth 3 -type f -name SKILL.md -path "*/$skill/SKILL.md" 2>/dev/null | head -1)"
  [ -n "$md" ] || continue
  if [ -n "$found_repo" ]; then
    echo "error: '$skill' exists in both $found_repo and $repo — one skill, one repo" >&2
    exit 2
  fi
  found_repo="$repo"
  found_md="$md"
done

if [ -z "$found_repo" ]; then
  printf "error: no skill named '%s' in any known repo:\n" "$skill" >&2
  printf '  %s\n' "${repos[@]}" >&2
  echo "If it belongs to another plugin, improve-skill stops with out-of-scope." >&2
  exit 1
fi

manifest="$found_repo/.claude-plugin/plugin.json"
market="$found_repo/.claude-plugin/marketplace.json"
plugin="$(sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$manifest" | head -1)"
marketplace="$(sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$market" | head -1)"

cat <<EOF
repo="$found_repo"
skill_md="$found_md"
manifest="$manifest"
plugin="$plugin"
marketplace="$marketplace"
update="claude plugin update $plugin@$marketplace"
EOF
