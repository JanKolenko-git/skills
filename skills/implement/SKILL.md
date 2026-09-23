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

One short paragraph: what was done, the PR link, the ticket's new status, warnings and
skipped steps, unresolved review findings, and whether the run was re-planned and why. When
`branch.path` is a worktree, it ends with the command that removes it.

## The pipeline

Data flows by the field names each skill declares. A value in hand is passed down, and
nothing refetches. `ticket.*` and `plan.*` stay in context for the whole run.

| #  | Skill | Wiring |
| --- | --- | --- |
| 1 | `jankolenko-skills:atlassian-jira` (+ `jankolenko-skills:atlassian-confluence`) | → `ticket.*`; 🛑 cannot fetch → stop, never a guessed ticket |
| 2 | `jankolenko-skills:find-repository` | skipped when `repo` is given; `ticket.title/description/components` → `hints`; → `repo.path`, made the session's directory; 🛑 ambiguous → stop with its candidates |
| 3 | `jankolenko-skills:plan` | `ticket.*` → `goal`/`criteria`/`candidates`/`constraints`; → `plan.*`; 🛑 verdict |
| 4 | `jankolenko-skills:git-create-branch` | `ticket.type/priority` → `type`; `ticket.title` → `slug`; `ticket.key` → `ticket_key`; → `branch.*`; 🛑 its gate when the checkout is busy; every later step runs in `branch.path` |
| 5 | `jankolenko-skills:atlassian-jira` | `mode=transition`, `In Progress`; a refusal is warned about, not fatal |
| 6 | inline + `jankolenko-skills:test` | `plan.steps`/`plan.lanes`; `ticket.acceptance_criteria` → `criteria` |
| 7 | `jankolenko-skills:test` | → `tests.result`; 🛑 three failed attempts → stop with the output; never weaken a test |
| 8a | `jankolenko-skills:check` | `plan.*` (in full: it runs in its own context) + `criteria` + diff → `check.verdict` |
| 8b | `/code-review` (`jankolenko-skills:review` when the user asked for a panel), `/simplify` | findings → 6, up to three rounds; what is left goes into the PR and the gate summary |
| 9 | `jankolenko-skills:git-commit` | `ticket.key` → `ticket_key`; `plan.summary` → `subject`; `Bug` → `fix`, else `feat` |
| 10 | `jankolenko-skills:git-pr-push-and-open` | `<ticket.key>: <ticket.title>` → `title`, under 70 characters; `summary_points` from the run; 🛑 its gate |
| 11 | `jankolenko-skills:atlassian-jira` | `In Review` (`Code Review` is a fine match); then comment `PR opened: <pr.url>. <one sentence>.` |
| 12 | `jankolenko-skills:record-learnings` | the run's surprises, `destination = repo`; most runs have nothing durable, skip quietly |

`/code-review` and `/simplify` are used if installed, else done inline with their angles
and noted once. `jankolenko-skills:atlassian-jira` is the hard dependency. Every bail-out
states what blocks, what was tried, and what would unblock it.

## Step 3 — Plan

Split the ticket: `goal` is the outcome (what is wrong now, what fixed looks like),
`candidates` any mechanism the ticket proposes. Passed whole, the proposed change becomes
the goal and the plan reasons about how to build it instead of whether to. A ticket naming
only a mechanism still has an outcome: state it, and say in the report that you inferred it.
The repo's `## Learned constraints` section of `CLAUDE.md`, if any, is `constraints`.

Route on `plan.verdict` before any branch or ticket change, so a run that should not have
started leaves no trace:

| `plan.verdict` | Do |
| --- | --- |
| `ready` | Continue |
| `no-change-needed` | No code change, no ticket change. Report the evidence |
| `blocked` | Bail out with `plan.open_questions`: the skill already settled facts and asked its one round of decisions. When it names a decision that outlives the ticket, say that `jankolenko-skills:architect` settles it and this run starts again after |

## Step 6 — Build

Work through `plan.steps`, tests written alongside. For a bug, confirm the test fails
before the fix. Named lanes may fan out to subagents, one lane each with its files, steps
and verification command. Fan out only when the lanes are substantial and the user has not
asked you to stay in-session. Read the combined diff yourself before the tests.

## Step 8 — Check, then review

The check runs first, because polishing code that should not exist is waste.

| `check.verdict` | Do |
| --- | --- |
| `accept` | Review (8b) |
| `reject-to-code` | Step 6, then 7, then check again |
| `reject-to-plan` | Step 3 with what the code revealed, branch and ticket untouched |
| `blocked` | Supply what it named and check again (`jankolenko-skills:walkthrough` with `scope=environment` when the app would not start), or carry the blocked behaviours into the gate summary |

Fix rounds that keep landing on one mechanism mean the mechanism fights the codebase. The
tell, from the check or the review: another edge-case branch, another stop condition,
another caller wired in to cooperate. The second such round goes to Step 3 as
`reject-to-plan`, not to a third patch. A second `reject-to-plan` on the same ticket means
the goal is not understood: bail out with both plans and what the code showed about each.

## Step 10 — Ship

> 🛑 `jankolenko-skills:git-pr-push-and-open` owns the review gate: it shows the diff and
> asks through `AskUserQuestion` before pushing. Do not push around it or answer for the
> user. Pass `push=waived` only when the user said so in chat at the start of this run.
> Standing rule: writes only on the user's word in chat. The gate summary includes anything
> unresolved from the review. It also lists each part's win against its code cost (lines
> added, shared files touched), so a marginal part can be cut before it ships.
