# 0006 — A bare verb when it names the job alone

**Status:** accepted · 2026-09-17 · amends [`0003-skill-naming.md`](./0003-skill-naming.md)

## Context

ADR 0003 fixed the shape `[<system>-]<verb>-<object>` and a lexicon in which one verb means
one thing. In use, the object earned nothing where the verb was already unique: `plan` what,
in a plugin with one planning skill? The reference set this repo was compared against
([jsmastery-pro/skills](https://github.com/jsmastery-pro/skills)) names every skill by a
bare verb, `scope`, `architect`, `develop`, `check`, `test`, `document`, `debug`, and reads
better for it. Three of its skills were wanted here (`debug`, `check`, `architect`), two more
were near-duplicates of skills already here under longer names (`test`, `implement`).

## Decision

**`[<system>-]<verb>[-<object>]`. The object is dropped when the verb is unique across both
plugins and still names the job without it.** Everything else in 0003 stands: the prefix
names a binding, the lexicon has one meaning per verb, words are spelt out, hyphens only.

| Before | After | Why |
| --- | --- | --- |
| `plan-change` | `plan` | The only `plan`; the object added nothing |
| `critique-plan` | `check` | Folded into a wider skill: intent, behaviour and a comparison against the base branch. `critique` leaves the lexicon |
| `diagnosing-bugs` | `debug` | The verb users type; rewritten to the house contract instead of mirrored |
| `write-tests` | `test` | The only test-writing skill; `write` leaves the lexicon |
| `implement-ticket` | `implement` | The lexicon already defined `implement` as the orchestrated build; the ticket is its default input |
| — | `architect` | New: a decision that outlives one change, recorded |
| — | `document` | New: prose about a change, from its diff |

Kept with their object: `find-repository`, `find-skill-gaps`, `find-session-improvements`
(`find` is shared three ways), `record-learnings` and `record-engineering-rule` (`record` is
shared), `draft-reply`, `prepare-local-environment` and `improve-skill` (the bare verb says
less than the object does), and every `git-` and `atlassian-` skill (the prefix is a binding).

## Consequences

- **Five slash commands change**, and the plugin ships as a major version, as 0003's renames
  and Batch A's removal did.
- **`architect` and `document` are user-invoked** (`disable-model-invocation: true`). They
  cost nothing in the skill listing, and an autonomous ticket run cannot make an
  architecture decision on its own: `plan` returns `blocked` naming the decision, and the
  user runs `/jankolenko-skills:architect`.
- **Three skills now compete with other plugins on the same prompts**: `debug` with
  `mattpocock-skills:diagnosing-bugs` and the engineering plugin's `debug`; `check` and `test`
  with that plugin's review and testing-strategy skills. Which one fires shows in use;
  disabling the mirror is the user's call now that `debug` replaces it.
- **The lexicon gains `check`, `test`, `debug`, `architect` and `document`** and loses
  `critique` and `write`.
- **Only the names that carried nothing changed.** The role vocabulary (atom, orchestrator),
  the named-field wiring, the verdicts and the gates are untouched; `check` keeps
  `critique-plan`'s four questions and its forked context, and adds the two things the
  signals ledger had asked for twice, evidence from a run and a comparison against the base.

## Alternatives considered

**Rename everything to bare verbs** (`improve`, `draft`, `prepare`, `find`). Rejected: `find`
and `record` are shared, and `improve`, `draft` and `prepare` alone say less than their
object; the session-start hook names `improve-skill` in every session.

**Merge `critique-plan` into `plan` as a mode.** Rejected: planning runs in the main context
because it asks decisions through `AskUserQuestion`, and the critique runs in a forked
context so the judge does not share the builder's reasoning. One file cannot be both.

**Adopt the reference set's `scope`, `audit` and `sync`.** Rejected: they maintain a
file-based state model (a scope file, spec statuses, `AGENTS.md`) that its other skills read
back. State here lives in Jira, Confluence and `CLAUDE.md`, covered by the Atlassian skills,
`record-learnings` and the built-in init. Their output-style block, portability sections and
`agents/openai.yaml` were not adopted either: the house style is stated once in
`authoring.md`, and the plugin runs in Claude Code only.
