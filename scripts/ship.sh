#!/usr/bin/env bash
set -uo pipefail

# Ship a change to either plugin: check → evals → bump → commit → the update command.
# This is the deploy loop every meta skill used to describe in prose. Sessions load skills
# from the versioned plugin cache, so an edit is invisible until the manifest is bumped and
# the plugin updated; this script owns that whole loop and refuses to bump on a red suite.
#
# Usage: scripts/ship.sh [-m <commit message>] [--minor | --major] [--no-evals] [--case <glob>]
#                        [--trigger] [--dry-run] <skill-name | general | projects>
#
#   <skill-name>  resolves the plugin that ships it (which-plugin.sh); evals default to
#                 the cases named after the skill (--case '<skill>-*') and, with --trigger,
#                 its trigger set against the baseline in evals/triggers/README.md
#   general       the jankolenko-skills plugin as a whole; evals default to the full suite
#   projects      the jankolenko-projects plugin; untracked, so bump and update only
#   -m            commit message; required for a tracked change unless --dry-run
#   --minor       bump the minor version (the skill set or plugin.json paths changed)
#   --major       bump the major version (a skill removed, a contract or gate changed shape)
#   --no-evals    skip the eval run (say why in the commit body)
#   --dry-run     show the target, version and staged files; change nothing
#
# Stage the files you changed first (`git add <path>`); this script stages only the manifest
# bump on top, so nothing lands in the commit that you did not put in the index yourself.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO" || exit 1

message=""; bump="patch"; run_evals=1; case_glob=""; trigger=0; dry_run=0; target=""
while [ $# -gt 0 ]; do
  case "$1" in
    -m) message="${2:-}"; shift 2 ;;
    --minor) bump="minor"; shift ;;
    --major) bump="major"; shift ;;
    --no-evals) run_evals=0; shift ;;
    --case) case_glob="${2:-}"; shift 2 ;;
    --trigger) trigger=1; shift ;;
    --dry-run) dry_run=1; shift ;;
    -h|--help) sed -n '3,23p' "$0"; exit 0 ;;
    -*) echo "ship.sh: unknown flag $1" >&2; exit 1 ;;
    *) target="$1"; shift ;;
  esac
done
[ -n "$target" ] || { echo "ship.sh: name a skill, or 'general' or 'projects'" >&2; exit 1; }

# --- 1. Resolve what ships from where -------------------------------------------------
case "$target" in
  general)
    repo="$REPO"; manifest="$REPO/.claude-plugin/plugin.json"; tracked=1
    plugin="jankolenko-skills"; update="claude plugin update jankolenko-skills@jankolenko"
    [ -n "$case_glob" ] || case_glob="*"
    ;;
  projects)
    repo="${JANKOLENKO_PROJECTS_DIR:-$REPO/projects}"; manifest="$repo/.claude-plugin/plugin.json"; tracked=0
    plugin="jankolenko-projects"; update="claude plugin update jankolenko-projects@jankolenko-projects"
    run_evals=0
    ;;
  *)
    resolved="$(scripts/which-plugin.sh "$target")" || exit 1
    eval "$resolved"   # repo, skill_md, manifest, plugin, marketplace, update, tracked
    [ -n "$case_glob" ] || case_glob="$target-*"
    ;;
esac
[ -f "$manifest" ] || { echo "ship.sh: no manifest at $manifest" >&2; exit 1; }

current="$(python3 -c "import json;print(json.load(open('$manifest'))['version'])")"
next="$(python3 - "$current" "$bump" <<'EOF'
import sys
major, minor, patch = (int(x) for x in sys.argv[1].split("."))
bump = sys.argv[2]
print(f"{major + 1}.0.0" if bump == "major" else f"{major}.{minor + 1}.0" if bump == "minor" else f"{major}.{minor}.{patch + 1}")
EOF
)"

echo "ship.sh: $plugin $current → $next ($bump), manifest $manifest, tracked=$tracked"
if [ "$tracked" -eq 1 ]; then
  staged="$(git diff --cached --name-only)"
  if [ -z "$staged" ] && [ "$dry_run" -eq 0 ]; then
    echo "ship.sh: nothing staged — git add the files you changed first" >&2; exit 1
  fi
  echo "ship.sh: staged:"; printf '   %s\n' $staged
fi

# --- 2. Checks and evals ---------------------------------------------------------------
if [ "$dry_run" -eq 1 ]; then
  echo "ship.sh: dry run — would run check.sh$( [ "$run_evals" -eq 1 ] && echo ", eval.sh --case '$case_glob'" )$( [ "$trigger" -eq 1 ] && echo ", trigger-eval.py --skill $target" ), then bump$( [ "$tracked" -eq 1 ] && echo " and commit" )"
  exit 0
fi

scripts/check.sh > /tmp/ship-check.log 2>&1 || { cat /tmp/ship-check.log; echo "ship.sh: check.sh failed — not bumping" >&2; exit 1; }
echo "ship.sh: check.sh green"

if [ "$run_evals" -eq 1 ]; then
  matches="$(ls -d evals/*/ 2>/dev/null | xargs -n1 basename | grep -vE '^(results|triggers)$' | grep -E "^${case_glob//\*/.*}$" || true)"
  if [ -z "$matches" ]; then
    echo "ship.sh: no eval case matches '$case_glob' — an uncovered gate; say so in the commit body"
  else
    echo "ship.sh: running evals: $(echo $matches | tr '\n' ' ')"
    scripts/eval.sh --case "$case_glob" --threshold 1 > /tmp/ship-eval.log 2>&1
    eval_status=$?
    tail -5 /tmp/ship-eval.log
    if [ "$eval_status" -ne 0 ]; then
      echo "ship.sh: evals red (exit $eval_status) — not bumping. Full log: /tmp/ship-eval.log" >&2; exit 1
    fi
    echo "ship.sh: evals green"
  fi
fi

if [ "$trigger" -eq 1 ] && [ -f "evals/triggers/$target.json" ]; then
  baseline="$(grep -E "^\| \`$target\` \|" evals/triggers/README.md | head -1)"
  scripts/trigger-eval.py --skill "$target" --json /tmp/ship-trigger.json | head -1
  python3 - "$baseline" <<'EOF' || { echo "ship.sh: trigger rate fell below the baseline — not bumping" >&2; exit 1; }
import json, re, sys
r = json.load(open("/tmp/ship-trigger.json"))["summary"]
m = re.findall(r"(\d+)/(\d+)", sys.argv[1])
if not m:
    print("ship.sh: no baseline row for this skill; recording nothing"); sys.exit(0)
base_pos = int(m[0][0]) / int(m[0][1]); base_neg = int(m[1][0]) / int(m[1][1])
pos = r["should_trigger"]["passed"] / max(r["should_trigger"]["total"], 1)
neg = r["should_not_trigger"]["passed"] / max(r["should_not_trigger"]["total"], 1)
print(f"ship.sh: trigger should-fire {pos:.0%} (baseline {base_pos:.0%}), near-miss {neg:.0%} (baseline {base_neg:.0%})")
sys.exit(0 if pos >= base_pos and neg >= base_neg else 1)
EOF
fi

# --- 3. Bump, commit, tell -------------------------------------------------------------
python3 - "$manifest" "$next" <<'EOF'
import json, sys
path, version = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
old = json.loads(text)["version"]
assert text.count(f'"version": "{old}"') == 1, "manifest version field is not where expected"
open(path, "w", encoding="utf-8").write(text.replace(f'"version": "{old}"', f'"version": "{version}"', 1))
EOF
echo "ship.sh: bumped $plugin to $next"

if [ "$tracked" -eq 1 ]; then
  [ -n "$message" ] || { echo "ship.sh: -m <message> is required to commit" >&2; exit 1; }
  git add "$manifest" && git commit -q -m "$message" || { echo "ship.sh: commit failed" >&2; exit 1; }
  echo "ship.sh: committed $(git log --oneline -1)"
else
  echo "ship.sh: $plugin is untracked — nothing to commit"
fi

echo
echo "Run this to make it live:"
echo "  $update"
