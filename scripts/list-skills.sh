#!/usr/bin/env bash
set -euo pipefail

# Lists every skill in the repo, and fails if the four places a skill must appear have
# drifted apart: the folder itself, its bucket README.md, the root README.md, and the
# `skills` array in .claude-plugin/plugin.json. See CLAUDE.md -> "What must stay in sync".
#
# Usage: scripts/list-skills.sh

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

status=0
note() { printf '  %-9s %s\n' "$1" "$2"; }

printf '%-14s %-38s %s\n' BUCKET SKILL NAME
printf '%s\n' "----------------------------------------------------------------------------"

while IFS= read -r skill_md; do
  dir="$(dirname "$skill_md")"
  skill="$(basename "$dir")"
  bucket="$(basename "$(dirname "$dir")")"
  name="$(sed -n 's/^name:[[:space:]]*//p' "$skill_md" | head -1)"

  printf '%-14s %-38s %s\n' "$bucket" "$skill" "$name"

  # Depth: skills/<bucket>/<skill>/SKILL.md and nothing deeper.
  if [ "$dir" != "skills/$bucket/$skill" ]; then
    note DEPTH "$dir is not skills/<bucket>/<skill>"; status=1
  fi

  # The folder name is the skill's name, verbatim.
  if [ "$name" != "$skill" ]; then
    note NAME "$dir declares 'name: $name'"; status=1
  fi

  # Listed in its bucket README, the root README, and the plugin manifest.
  [ -f "skills/$bucket/README.md" ] || { note README "skills/$bucket/README.md is missing"; status=1; }
  grep -qF "](./$skill/SKILL.md)" "skills/$bucket/README.md" 2>/dev/null \
    || { note README "$skill not linked in skills/$bucket/README.md"; status=1; }
  grep -qF "](./skills/$bucket/$skill/SKILL.md)" README.md \
    || { note README "$skill not linked in the root README.md"; status=1; }
  grep -qF "\"./skills/$bucket/$skill\"" .claude-plugin/plugin.json \
    || { note PLUGIN "$skill not in plugin.json's skills array"; status=1; }
done < <(find skills -name SKILL.md | sed 's|^\./||' | sort)

# And the reverse: nothing in the manifest that no longer exists on disk.
while IFS= read -r path; do
  [ -f "$path/SKILL.md" ] || { note PLUGIN "plugin.json lists $path, which has no SKILL.md"; status=1; }
done < <(sed -n 's|.*"\./\(skills/[^"]*\)".*|\1|p' .claude-plugin/plugin.json)

echo
if [ "$status" -eq 0 ]; then
  echo "OK — $(find skills -name SKILL.md | wc -l | tr -d ' ') skills, no drift."
else
  echo "DRIFT — see the notes above." >&2
fi
exit "$status"
