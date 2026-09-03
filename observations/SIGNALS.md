# Skill-gap signals

The cross-session friction ledger. When a session notices a **missing capability** — not a
broken skill, that goes to `improve-skill` — it appends one line here, no approval needed.
`find-skill-gaps` reads this file and proposes a new skill only when a gap has **two or more
independent dated signals**.

One line per signal:

```
- YYYY-MM-DD · <where: repo or task> · <what was missing or repeated, one sentence>
```

Examples of what belongs here: the user pasted the same context or credentials by hand again,
a system had to be driven manually that has an API, a task shape recurred that no skill
covers. What does not belong here: one-off annoyances, friction with an existing skill's
wording (→ `improve-skill`), anything a signal line would leak a secret into.

When `find-skill-gaps` acts on a cluster, it moves those lines to **Resolved** below with the
outcome.

## Open signals

<!-- append below this line -->

- 2026-09-03 · monthly work report · Rebuilt "what did I do last month" by hand from git logs, PR lists and session transcripts across 11 repos; the same request was made on 2026-08-03 for July.

## Resolved

<!-- moved here by find-skill-gaps, with outcome -->
