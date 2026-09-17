#!/usr/bin/env bash
set -euo pipefail

# Answers "which plugin ships this skill, and where is its source?" — the question every
# meta skill has to get right now that two plugins ship from one working tree: the general
# one (this repo) and the project one (the untracked projects/ folder inside it).
#
# Prints shell-assignable lines: repo, skill_md, manifest, plugin, marketplace, update,
# tracked, scripts (this repo's scripts/ in the working copy, so a skill can run ship.sh
# from anywhere). Reach this script through the plugin's own copy —
# "${CLAUDE_SKILL_DIR}/../../../scripts/which-plugin.sh" — it locates the working copy;
# the cache copy is never what gets edited. `tracked` is 1 when $repo is under version control (commit the edit) and 0 when
# it is the untracked projects/ folder (bump the manifest in place; nothing to commit).
# Exits 1 if the skill is in neither, 2 if it is somehow in both.
#
# Usage: scripts/which-plugin.sh <skill-name>
#        source /dev/stdin <<< "$(scripts/which-plugin.sh plan)" && echo "$update"

skill="${1:-}"
if [ -z "$skill" ]; then
  echo "usage: $(basename "$0") <skill-name>" >&2
  exit 1
fi

# The env override wins; then the working copy you are inside, so a clone anywhere — and a
# copy on another machine, whose home is throwaway — resolves to itself; then the
# default location.
skills_repo="${JANKOLENKO_SKILLS_REPO:-}"
if [ -z "$skills_repo" ]; then
  here="$PWD"
  while [ "$here" != "/" ] && [ -n "$here" ]; do
    if [ -d "$here/skills" ] && [ -f "$here/.claude-plugin/plugin.json" ] \
       && grep -q '"name"[[:space:]]*:[[:space:]]*"jankolenko-skills"' "$here/.claude-plugin/plugin.json"; then
      skills_repo="$here"; break
    fi
    here="$(dirname "$here")"
  done
fi
skills_repo="${skills_repo:-$HOME/Developer/skills}"
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

# printf rather than a heredoc: a heredoc needs a temp file, which a sandboxed session
# may not be allowed to create.
printf '%s\n' \
  "repo=\"$found_repo\"" \
  "skill_md=\"$found_md\"" \
  "manifest=\"$manifest\"" \
  "plugin=\"$plugin\"" \
  "marketplace=\"$marketplace\"" \
  "update=\"claude plugin update $plugin@$marketplace\"" \
  "tracked=$found_tracked" \
  "scripts=\"$skills_repo/scripts\""
