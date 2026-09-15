#!/usr/bin/env bash
set -uo pipefail

# Prints the spine of a session transcript: the user's own turns (first line of each), the
# skills that ran and how often, and how many times the run was interrupted. A transcript
# runs to megabytes, most of it tool output the session already saw and the injected body of
# every skill that ran; this is what a retrospective needs from it, and nothing else.
#
# Usage: scripts/session-spine.sh <session-id> [project-dir]
#        project-dir defaults to the current directory; the transcript lives at
#        ~/.claude/projects/<project-dir with / replaced by ->/<session-id>.jsonl

id="${1:-}"
[ -n "$id" ] || { echo "usage: $(basename "$0") <session-id> [project-dir]" >&2; exit 1; }
dir="${2:-$PWD}"
slug="$(printf '%s' "$dir" | sed 's|/|-|g')"
t="$HOME/.claude/projects/$slug/$id.jsonl"
[ -f "$t" ] || { echo "no transcript at $t" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }

echo "== user turns (first line each)"
jq -r 'select(.type=="user") | .message.content
       | if type=="array" then (.[]? | select(.type=="text") | .text) else . end
       | select(type=="string") | split("\n")[0][0:160]' "$t" 2>/dev/null \
  | grep -v '^Base directory for this skill:' \
  | grep -vE '^\[Request interrupted|^<task-notification>|^\[SYSTEM NOTIFICATION' || true

echo
echo "== skills that ran"
grep -oE 'Base directory for this skill: [^"]*/skills/[a-zA-Z0-9/._-]+' "$t" \
  | sed 's|.*/skills/||' | sort | uniq -c | sort -rn || true

echo
echo "== interruptions: $(grep -c 'Request interrupted by user' "$t" 2>/dev/null || echo 0)"
