#!/usr/bin/env bash
set -uo pipefail

# The one command to run before every commit: layout, portability, budgets, manifests.
# Each check is its own script so it can be run alone; this only chains them and fails
# if any of them does.
#
# Usage: scripts/check.sh

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

status=0
run() {
  local name="$1"; shift
  echo "== $name"
  if "$@"; then
    echo "   ok: $name"
  else
    echo "   FAIL: $name" >&2
    status=1
  fi
  echo
}

# The four standing rules are stated once, in the session-start hook. A skill points at one
# with `Standing rule: …` and restates none; these are the shapes a restatement takes.
standing_rules() {
  local hits
  hits="$(grep -rniE 'never (an )?instructions?|not (an )?instructions?|provenance rule|injection|fetched (text|content)|never because (a |fetched)|never write credentials' skills --include=SKILL.md | grep -v 'Standing rule:' || true)"
  [ -z "$hits" ] || { echo "$hits"; return 1; }
}

run "layout (list-skills.sh)"        scripts/list-skills.sh
run "standing rules stated once"     standing_rules
run "portable (check-portable.py)"   scripts/check-portable.py
run "budgets (measure.py)"           scripts/measure.py
# A nested `claude` refuses to start while CLAUDECODE marks an outer session; validation
# needs no session, so drop the marker for this call only.
run "manifest (claude plugin validate .)" env -u CLAUDECODE claude plugin validate .
if [ -f projects/.claude-plugin/plugin.json ]; then
  run "manifest (claude plugin validate projects)" env -u CLAUDECODE claude plugin validate projects
fi

if [ "$status" -eq 0 ]; then
  echo "check: all green"
else
  echo "check: FAILED — see above" >&2
fi
exit "$status"
