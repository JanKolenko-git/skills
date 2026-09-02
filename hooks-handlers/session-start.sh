#!/usr/bin/env bash
# Standing rule for the skill-layer feedback loop. Kept short: this text is paid for
# in every session. The mechanics live in the meta skills, not here.

SKILLS_REPO="${JANKOLENKO_SKILLS_REPO:-$HOME/Developer/skills}"

cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Engineering rules (jankolenko-skills): before writing or changing code in any repo, read ${SKILLS_REPO}/ENGINEERING.md once — short, cross-cutting rules that the output of every one of your skills follows.\n\nSkill-layer feedback loop (jankolenko-skills): while any of your own skills runs, watch for friction — wording that misled you, an input that was missing, a step that fought the task, or an idea that would make the skill better. Note it silently; NEVER interrupt the work for it. When the run's real work is done, raise at most one consolidated block: (1) friction with one of your own skills, in either the jankolenko-skills or jankolenko-projects plugin → offer to run jankolenko-skills:improve-skill with the specific observation; (2) a capability that does not exist — the user repeated the same manual context or chore, a system with an API was driven by hand, a task shape recurred that no skill covers → append one dated line under '## Open signals' in ${SKILLS_REPO}/observations/SIGNALS.md (no approval needed for the append; never write secrets into it) and mention it in one sentence. If the same gap already has a signal from an earlier date, suggest running jankolenko-skills:find-skill-gaps; (3) a coding convention the work got wrong that no rule in ENGINEERING.md covered \u2014 offer to run jankolenko-skills:record-engineering-rule with the specific failure. Do not edit any skill or draft a new one from this rule alone — jankolenko-skills:improve-skill and jankolenko-skills:find-skill-gaps own those mechanics and their gates. If no friction was observed, say nothing about any of this."
  }
}
EOF
exit 0
