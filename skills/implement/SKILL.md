---
name: implement
description: Implement a Jira ticket end to end: fetch it and its specs, find the repo, plan, branch, build with tests, check against plan and base, stop for human review, then push, open the PR and move it to In Review. Use when the user asks to implement, solve, work on or take to in review a ticket by key or URL. Reading a ticket is atlassian-jira.
argument-hint: <ticket-key | jira-url> [repo] [push=ask|waived]
---

# Implement

Take a ticket from assigned to in review. This skill is an **orchestrator**: the atoms do
the work, and this file is the wiring, what each atom is called with and where its output
goes next.

## Inputs

- `ticket_key` — **required.** A ticket key (`PROJ-1234`) or any Jira URL containing one.
- `repo` — optional. Skips repo discovery when the user already named one.
- `push` — optional. `ask` (default) or `waived`, when the user said up front, in chat, not
  to stop before pushing.

## Output

A short report: what was implemented, the PR URL, the ticket's new status, anything skipped
or unresolved.

## The pipeline

Data flows by the field names each skill declares; a value in hand is passed down, nothing
refetches. `ticket.*` and `plan.*` stay in context for the whole run.

| #  | Skill | Wiring |
| --- | --- | --- |
| 1 | `jankolenko-skills:atlassian-jira` (+ `jankolenko-skills:atlassian-confluence`) | → `ticket.*`; 🛑 cannot fetch → stop, never a guessed ticket |
| 2 | `jankolenko-skills:find-repository` | skipped when `repo` is given; `ticket.title/description/components` → `hints`; → `repo.path`, `cd` there; 🛑 ambiguous → stop with its candidates |
| 3 | `jankolenko-skills:plan` | `ticket.*` → `goal`/`criteria`/`candidates`/`constraints`; → `plan.*`; 🛑 verdict |
| 4 | `jankolenko-skills:git-create-branch` | `ticket.type/priority` → `type`; `ticket.title` → `slug`; `ticket.key` → `ticket_key` |
| 5 | `jankolenko-skills:atlassian-jira` | `mode=transition`, `In Progress`; a refusal is warned about, not fatal |
| 6 | inline + `jankolenko-skills:test` | `plan.steps`/`plan.lanes`; `ticket.acceptance_criteria` → `criteria` |
| 7 | `jankolenko-skills:test` | → `tests.result`; 🛑 three failed attempts → stop with the output; never weaken a test |
| 8a | `jankolenko-skills:check` | `plan.*` (in full: it runs in its own context) + `criteria` + diff → `check.verdict` |
| 8b | `/code-review`, `/simplify` | findings → 6, up to three rounds; what is left goes into the PR and the gate summary |
| 9 | `jankolenko-skills:git-commit` | `ticket.key` → `ticket_key`; `plan.summary` → `subject`; `Bug` → `fix`, else `feat` |
| 10 | `jankolenko-skills:git-pr-push-and-open` | `<ticket.key>: <ticket.title>` → `title`, under 70 characters; `summary_points` from the run; 🛑 its gate |
| 11 | `jankolenko-skills:atlassian-jira` | `In Review` (`Code Review` is a fine match); then comment `PR opened: <pr.url>. <one sentence>.` |
| 12 | `jankolenko-skills:record-learnings` | the run's surprises, `destination = repo`; most runs have nothing durable, skip quietly |

`/code-review` and `/simplify` are used if installed, else done inline with their angles
and noted once; `jankolenko-skills:atlassian-jira` is
the hard dependency. Every bail-out states what blocks, what was tried, and what would
unblock it.

## Step 3 — Plan

Split the ticket: `goal` is the outcome (what is wrong now, what fixed looks like),
`candidates` any mechanism the ticket proposes. Passed whole, the proposed change becomes
the goal and the plan reasons about how to build it instead of whether to. A ticket naming
only a mechanism still has an outcome; state it and say in the report that you inferred it.
The repo's `## Learned constraints` section of `CLAUDE.md`, if any, is `constraints`.

Route on `plan.verdict` before any branch or ticket change, so a run that should not have
started leaves no trace: `blocked` → the skill already settled facts and asked its one
round of decisions, so bail out with `plan.open_questions`, and when it names a decision
that outlives the ticket, say that `jankolenko-skills:architect` settles it and this run
starts again after; `no-change-needed` → no code change, no ticket change, report the
evidence; `ready` → continue.

## Step 6 — Build

Work through `plan.steps` in the conventions of the file being edited, tests written
alongside; for a bug, confirm the test fails before the fix. `plan.lanes = none` builds
serially. Named lanes may fan out to subagents, one lane each with its files, steps and
verification command, only when they are substantial and the user has not asked you to
stay in-session; read the combined diff yourself before the tests.

## Step 8 — Check, then review

The check runs first, because polishing code that should not exist is waste, and it runs
the change and compares the base branch so a regression is caught before a reviewer sees
it. `reject-to-plan` → Step 3 with what the code revealed, branch and ticket untouched;
`reject-to-code` → Step 6, then 7, then check again; `blocked` → supply what it named
(`jankolenko-skills:prepare-local-environment` when the app would not start), check again,
or carry the blocked behaviours into the gate summary; `accept` → review. A second
`reject-to-plan` on the same ticket means the goal is not understood: bail out with both
plans and what the code showed about each.

## Step 10 — Ship

> 🛑 `jankolenko-skills:git-pr-push-and-open` owns the review gate: it shows the diff and
> asks through `AskUserQuestion` before pushing. Do not push around it or answer for the
> user. Pass `push=waived` only when the user said so in chat at the start of this run.
> Standing rule: writes only on the user's word in chat. Include anything unresolved from
> the review in the gate summary.

## Final report

One short paragraph: what was done, the PR link, the ticket's new status, warnings and
skipped steps, unresolved review findings, and whether the run was re-planned and why.
