#!/usr/bin/env bash
# Standing rule for the skill-layer feedback loop. Kept short: this text is paid for
# in every session. The mechanics live in the meta skills, not here.

SKILLS_REPO="${JANKOLENKO_SKILLS_REPO:-$HOME/Developer/skills}"

# The working copy is the good source — it is what improve-skill edits. But a session
# can run where it does not exist (an eval sandbox, another machine, a cloud agent),
# and both clauses below name paths inside it. Fall back to the plugin cache, which
# ships the same two files, and stay silent rather than point at a path that is not
# there: a rule telling the agent to read a missing file costs turns and teaches it
# to ignore the rule.
if [ ! -f "$SKILLS_REPO/ENGINEERING.md" ]; then
  SKILLS_REPO="${CLAUDE_PLUGIN_ROOT:-$SKILLS_REPO}"
fi
[ -f "$SKILLS_REPO/ENGINEERING.md" ] || exit 0

# Project rules live in projects/<repository>/ENGINEERING.md, keyed by the repository the
# session opened in. The remote's name is tried first because a worktree's folder carries a
# suffix the remote does not; the toplevel folder name is the fallback for a repo with no
# remote. Same silence rule: no match, no pointer.
PROJECTS_DIR="${JANKOLENKO_PROJECTS_DIR:-$SKILLS_REPO/projects}"
PROJECT_RULES=""
WORK_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
if [ -d "$PROJECTS_DIR" ]; then
  toplevel="$(git -C "$WORK_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -n "$toplevel" ]; then
    remote="$(git -C "$WORK_DIR" remote get-url origin 2>/dev/null || true)"
    remote="${remote%.git}"
    for name in "${remote##*[/:]}" "${toplevel##*/}"; do
      if [ -n "$name" ] && [ -f "$PROJECTS_DIR/$name/ENGINEERING.md" ]; then
        PROJECT_RULES="$PROJECTS_DIR/$name/ENGINEERING.md"
        break
      fi
    done
  fi
fi

PROJECT_CLAUSE=""
if [ -n "$PROJECT_RULES" ]; then
  PROJECT_CLAUSE=" Then read ${PROJECT_RULES} once — the rules that hold in this repository but not everywhere, and the evidence this repository bought for the general ones."
fi

cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Engineering rules (jankolenko-skills): before writing or changing code in any repo, read ${SKILLS_REPO}/ENGINEERING.md once — short, cross-cutting rules that the output of every one of your skills follows.${PROJECT_CLAUSE}\n\nSkill-layer feedback loop (jankolenko-skills): while any of your own skills runs, watch for friction — wording that misled you, an input that was missing, a step that fought the task, or an idea that would make the skill better. Note it silently; NEVER interrupt the work for it. When the run's real work is done, raise at most one consolidated block: (1) friction with one of your own skills, in either the jankolenko-skills or jankolenko-projects plugin → offer to run jankolenko-skills:improve-skill with the specific observation; (2) a capability that does not exist — the user repeated the same manual context or chore, a system with an API was driven by hand, a task shape recurred that no skill covers → append one dated line under '## Open signals' in ${SKILLS_REPO}/observations/SIGNALS.md (no approval needed for the append; never write secrets, repo names, tickets or PR numbers into it) and mention it in one sentence. If the same gap already has a signal from an earlier date, suggest running jankolenko-skills:find-skill-gaps; (3) a coding convention the work got wrong that no rule covered — offer to run jankolenko-skills:record-engineering-rule with the specific failure; it decides whether the rule is general (ENGINEERING.md, which names the shape of a failure and never a repo, ticket, PR or commit) or belongs to this repository (projects/<repository>/ENGINEERING.md, where the identifiers are the point). Do not edit any skill or draft a new one from this rule alone — jankolenko-skills:improve-skill and jankolenko-skills:find-skill-gaps own those mechanics and their gates. If no friction was observed, say nothing about any of this."
  }
}
EOF
exit 0
