#!/usr/bin/env bash
set -uo pipefail

# Prints the spine of a session transcript: the user's own turns (first line of each), the
# skills that ran and how often, and how many times the run was interrupted. A transcript
# runs to megabytes, most of it tool output the session already saw and the injected body of
# every skill that ran; this is what a retrospective needs from it, and nothing else.
#
# Usage: session-spine.sh <session-id> [project-dir]
#        project-dir defaults to the current directory; the transcript lives at
#        ~/.claude/projects/<project-dir, non-alphanumerics replaced by ->/<session-id>.jsonl
#        session-spine.sh --since <date>
#        one spine per session with turns on or after <date>, every project, oldest first

command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }

# The user's text blocks in a transcript, first line each, on or after $2 ("" keeps them all).
user_text() {
  jq -r --arg since "$2" 'select(.type=="user" and ($since=="" or .timestamp >= $since))
         | .message.content
         | if type=="array" then (.[]? | select(.type=="text") | .text) else . end
         | select(type=="string") | split("\n")[0]' "$1" 2>/dev/null
}

spine() {
  local t="$1" since="$2"
  echo "== user turns (first line each)"
  user_text "$t" "$since" | cut -c1-160 \
    | grep -v '^Base directory for this skill:' \
    | grep -vE '^\[Request interrupted|^<task-notification>|^\[SYSTEM NOTIFICATION|^<local-command' || true
  echo
  echo "== skills that ran"
  user_text "$t" "$since" | grep -oE '^Base directory for this skill: .*/skills/[a-zA-Z0-9/._-]+' \
    | sed 's|.*/skills/||' | sort | uniq -c | sort -rn || true
  echo
  echo "== interruptions: $(user_text "$t" "$since" | grep -c '^\[Request interrupted by user' || true)"
}

if [ "${1:-}" = "--since" ]; then
  since="${2:-}"
  [ -n "$since" ] || { echo "usage: $(basename "$0") --since <date>" >&2; exit 1; }
  # mtime is never earlier than the last turn, so this is a cheap superset; jq does the rest
  find "$HOME/.claude/projects" -mindepth 2 -maxdepth 2 -name '*.jsonl' -newermt "$since" \
    | while read -r t; do
        first="$(jq -r --arg since "$since" 'select(.type=="user" and .timestamp >= $since)
                   | .timestamp' "$t" 2>/dev/null | head -1)"
        [ -n "$first" ] && printf '%s\t%s\n' "$first" "$t"
      done | sort | while IFS=$'\t' read -r first t; do
        echo
        echo "=== ${first:0:16} $(basename "$(dirname "$t")") $(basename "$t" .jsonl | cut -c1-8)"
        spine "$t" "$since"
      done
  exit 0
fi

id="${1:-}"
[ -n "$id" ] || { echo "usage: $(basename "$0") <session-id> [project-dir] | --since <date>" >&2; exit 1; }
dir="${2:-$PWD}"
slug="$(printf '%s' "$dir" | sed 's|[^A-Za-z0-9]|-|g')"
t="$HOME/.claude/projects/$slug/$id.jsonl"
[ -f "$t" ] || { echo "no transcript at $t" >&2; exit 1; }
spine "$t" ""
