#!/usr/bin/env bash
set -euo pipefail

# Answers "which plugin ships this skill, and where is its source?" — the question every
# meta skill has to get right now that two plugins ship from one working tree: the general
# one (this repo) and the project one (the untracked projects/ folder inside it).
#
# Prints shell-assignable lines: repo, skill_md, manifest, plugin, marketplace, update,
# tracked. `tracked` is 1 when $repo is under version control (commit the edit) and 0 when
# it is the untracked projects/ folder (bump the manifest in place; nothing to commit).
# Exits 1 if the skill is in neither, 2 if it is somehow in both.
#
# Usage: scripts/which-plugin.sh <skill-name>
#        eval "$(scripts/which-plugin.sh plan-change)" && echo "$update"

skill="${1:-}"
if [ -z "$skill" ]; then
  echo "usage: $(basename "$0") <skill-name>" >&2
  exit 1
fi

# Both roots are overridable so a clone anywhere still works.
skills_repo="${JANKOLENKO_SKILLS_REPO:-$HOME/Developer/skills}"
projects_dir="${JANKOLENKO_PROJECTS_DIR:-$skills_repo/projects}"

found_repo=""
found_md=""
found_tracked=""

# General plugin: skills/<bucket>/<skill>/SKILL.md — one bucket level, never two.
if [ -d "$skills_repo/skills" ]; then
  md="$(find "$skills_repo/skills" -mindepth 3 -maxdepth 3 -type f -name SKILL.md -path "*/$skill/SKILL.md" 2>/dev/null | head -1)"
  if [ -n "$md" ]; then
    found_repo="$skills_repo"
    found_md="$md"
    found_tracked=1
  fi
fi

# Project plugin: <repository>/skills/<skill>/SKILL.md — one repository folder deep.
if [ -d "$projects_dir" ]; then
  md="$(find "$projects_dir" -mindepth 4 -maxdepth 4 -type f -name SKILL.md -path "*/skills/$skill/SKILL.md" 2>/dev/null | head -1)"
  if [ -n "$md" ]; then
    if [ -n "$found_repo" ]; then
      echo "error: '$skill' exists in both $found_repo and $projects_dir — one skill, one plugin" >&2
      exit 2
    fi
    found_repo="$projects_dir"
    found_md="$md"
    found_tracked=0
  fi
fi

if [ -z "$found_repo" ]; then
  printf "error: no skill named '%s' in either plugin root:\n" "$skill" >&2
  printf '  %s\n' "$skills_repo" "$projects_dir" >&2
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
tracked=$found_tracked
EOF
