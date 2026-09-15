#!/usr/bin/env bash
# Builds a working copy of this skills repo for the case to run in. improve-skill's Step 1
# resolves the copy (the working copy you are inside wins in scripts/which-plugin.sh), so a
# fixture is never refused as "not ours", and a failed gate edits the copy and nothing else.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
src=""
for candidate in "$here/../.." "${JANKOLENKO_SKILLS_REPO:-}" "$HOME/Developer/skills"; do
  if [ -n "$candidate" ] && [ -f "$candidate/.claude-plugin/plugin.json" ] && [ -d "$candidate/skills" ]; then
    src="$(cd "$candidate" && pwd)"; break
  fi
done
[ -n "$src" ] || { echo "scaffold: no skills repo found near $here" >&2; exit 1; }

for entry in .claude-plugin .agents skills scripts hooks hooks-handlers observations ENGINEERING.md README.md; do
  cp -R "$src/$entry" .
done
mkdir -p evals && cp "$src/evals/README.md" evals/
git init -q . 2>/dev/null && git add -A >/dev/null 2>&1 \
  && git -c user.email=e@x -c user.name=n commit -qm "working copy" >/dev/null 2>&1 || true
