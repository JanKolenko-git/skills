# Meta

Skills that operate on the skill layer itself. They read and edit **this** repo — never a
work repo. That boundary is the membership test: a skill that changes application code
belongs in `engineering/`, not here.

Together they close the loop `record-learnings` closes for work repos. A session-start hook
(in [`hooks/`](../../hooks)) injects one standing rule: while any skill from this plugin runs,
friction is noted silently and raised **once, at the end of the run** — never mid-pipeline.
## Atoms

Each owns exactly one destination for that friction.

- **[improve-skill](./improve-skill/SKILL.md)** — Fix one of this repo's skills from an
  observed friction. Shows the exact diff, 🛑 stops for approval, then commits, bumps the
  version and tells you to `plugin update` so the fix actually ships.
- **[find-skill-gaps](./find-skill-gaps/SKILL.md)** — Read the cross-session ledger in
  [`observations/SIGNALS.md`](../../observations/SIGNALS.md) and propose a **new** skill only
  on two independent signals — 🛑 gated on the idea before drafting, and on the draft before
  it lands.
- **[record-engineering-rule](./record-engineering-rule/SKILL.md)** — Decide whether a coding
  run learned something that belongs in [`ENGINEERING.md`](../../ENGINEERING.md). Routes most
  candidates to `record-learnings` or `improve-skill` instead, and 🛑 gates the rest.

## Orchestrators

- **[find-session-improvements](./find-session-improvements/SKILL.md)** — Sweep a finished
  session for what the skill layer should have learned from it, and route each finding to
  the atom that owns it behind a single 🛑 triage gate. It covers the case the standing rule
  cannot: in a long session, noticing friction depends on recall, and recall is the first
  thing compaction drops — so this one re-derives the findings from the transcript instead.

All four are bound by [`.agents/authoring.md`](../../.agents/authoring.md), which defers
generic skill-writing mechanics to `anthropic-skills:skill-creator` through one swappable
reference.
