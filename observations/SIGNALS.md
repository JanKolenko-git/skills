# Skill-gap signals

The cross-session friction ledger. When a session notices a **missing capability** — not a
broken skill, that goes to `jankolenko-skills:improve-skill` — it appends one line here, no
approval needed. `jankolenko-skills:find-skill-gaps` reads this file and proposes a new skill
only when a gap has **two or more independent dated signals**.

One line per signal:

```
- YYYY-MM-DD · <context: the kind of task, never a repository or ticket> · <what was missing or repeated, one sentence>
```

Examples of what belongs here: the user pasted the same context or credentials by hand again,
a system had to be driven manually that has an API, a task shape recurred that no skill
covers. What does not belong here: one-off annoyances, friction with an existing skill's
wording (→ `jankolenko-skills:improve-skill`), anything a signal line would leak a secret
into, and any repository name, ticket key or PR number — this file is tracked and general,
so a signal describes the kind of task; the run's coordinates go in that repository's
`projects/<repository>/ENGINEERING.md` if they are worth keeping at all.

When `jankolenko-skills:find-skill-gaps` acts on a cluster, it moves those lines to
**Resolved** below with the outcome.

## Open signals

<!-- append below this line -->

- 2026-09-07 · a comment on someone else's PR · Posted a diagnosis before confirming it — named a likely cause for an analytics beacon that "didn't send", then a live test showed a duration cap was the actual cause and the comment had to be corrected publicly. No skill governs writing an unprompted finding to a shared surface: `jankolenko-skills:git-pr-address-review` covers replying to someone else's review comment, nothing covers the confidence bar for a claim you raise yourself.

- 2026-09-03 · monthly work report · Rebuilt "what did I do last month" by hand from git logs, PR lists and session transcripts across a dozen repos; the same request was made on 2026-08-03 for July.

## Resolved

<!-- moved here by find-skill-gaps, with outcome -->
