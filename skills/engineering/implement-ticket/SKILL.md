---
name: implement-ticket
description: Implement a Jira ticket end-to-end — fetches the ticket and its linked Confluence specs, finds the target repo, plans the change, branches, implements it with tests, critiques the diff against the plan, self-reviews, then STOPS for human review before pushing; on approval opens a PR, moves the ticket to In Review and records what the run learned. Bails out when the ticket is too ambiguous to act on. Use when the user runs /implement-ticket or asks to "implement", "solve" or "work on" a ticket by key or URL.
argument-hint: <ticket-key | jira-url> [repo] [push=ask|waived]
---

# Implement Ticket

Take a ticket from "assigned" to "in review": read it, build it, test it, ship it.

This skill is an **orchestrator**. It owns almost no mechanics of its own — the atoms do the
work, and this file's real job is the **wiring**: deciding what each atom is called with and
where its output goes next.

## Inputs

- `ticket_key` — **required.** A ticket key (`PROJ-1234`) or any Jira URL containing one.
- `repo` — optional. Skips repo discovery when the user already named one.
- `push` — optional. `ask` (default) or `waived`, when the user said up front not to stop
  before pushing.

## Output

A short report: what was implemented, the PR URL, the ticket's new status, and anything
skipped or unresolved.

## The pipeline

Data flows by the field names each skill declares. Where a value is already in hand, it is
passed down — nothing refetches.

| #   | Step      | Skill                            | Wiring                                                                             |
| --- | --------- | -------------------------------- | ---------------------------------------------------------------------------------- |
| 1   | Context   | `jankolenko-skills:atlassian-jira` (+ `jankolenko-skills:atlassian-confluence`)          | → `ticket.*`                                                                       |
| 2   | Repo      | `jankolenko-skills:find-repository`                      | `ticket.title/description` → `hints`; → `repo.path`                                |
| 3   | Plan      | `jankolenko-skills:plan-change` (+ `jankolenko-skills:clarify-goal`) | `ticket.*` → `goal`/`criteria`; → `plan.*`; `blocked` → `jankolenko-skills:clarify-goal` 🛑 **gate** |
| 4   | Branch    | `jankolenko-skills:git-create-branch`                  | `ticket.type/priority` → `type`; `ticket.title` → `slug`                           |
| 5   | Start     | `jankolenko-skills:atlassian-jira`                           | `mode=transition`, `target_status="In Progress"`                                   |
| 6   | Build     | _(inline)_ + `jankolenko-skills:write-tests`       | `plan.steps`/`plan.lanes`; `criteria` → `jankolenko-skills:write-tests`                              |
| 7   | Verify    | `jankolenko-skills:write-tests`                    | → `tests.result`                                                                   |
| 8a  | Critique  | `jankolenko-skills:critique-plan`                  | `plan.*` + diff → `critique.verdict` routes back to 3 or 6                         |
| 8b  | Review    | `/code-review`, `/simplify`      | findings → back to step 6                                                          |
| 9   | Commit    | `jankolenko-skills:git-commit`                    | `ticket.key` → `ticket_key`; `plan.summary` → `subject`                            |
| 10  | Ship      | `jankolenko-skills:git-pr-push-and-open`                        | `ticket.key + ticket.title` → `title` 🛑 **gate**                                  |
| 11  | Close out | `jankolenko-skills:atlassian-jira`                           | `target_status="In Review"`, `pr.url` → comment                                    |
| 12  | Learn     | `jankolenko-skills:record-learnings`               | run's surprises → `CLAUDE.md` / spec / ticket                                      |

The edge from 8a back to 3 is what makes this a loop rather than a line: a plan that the code
proves wrong gets replaced, not defended.

**Optional dependencies.** `mattpocock-skills:codebase-design`, `/code-review` and
`/simplify` are used **if installed**. If one is missing — or is installed but cannot run
as written here, e.g. it mandates subagents and the session forbids them — do that step
inline, keeping whatever angles it specifies, and note it once. Never fail the run over a
dependency you cannot invoke, and never let a delegated skill's mechanic override a
standing rule of the session. `jankolenko-skills:atlassian-jira` is the exception: without it there is no ticket, so
step 1 stops.

## Bail-out

Several steps below can stop the run. When bailing out, state plainly: what is blocking,
what you already tried, and what input would unblock it. Do not half-implement a ticket you
do not understand.

## Step 1 — Build the ticket context

Invoke **`jankolenko-skills:atlassian-jira`** with `ticket_key`, in `read` mode. It fetches the ticket,
attachments (viewing images), related tickets one level deep, and hands Confluence links to
**`jankolenko-skills:atlassian-confluence`** itself.

> 🛑 **GATE:** If `jankolenko-skills:atlassian-jira` cannot fetch the ticket, STOP: "Cannot fetch Jira ticket
> data." Never proceed on a guessed ticket.

Keep the resulting `ticket.*` fields in context for the whole run. Everything downstream
reads from them.

## Step 2 — Find the repository

Skip if `repo` was given, or if the current directory is already the right repo.

Otherwise invoke **`jankolenko-skills:find-repository`**, passing `ticket.title`, `ticket.description` and any
components or labels as `hints`. Do **not** pass `ticket_key` — you already hold the ticket,
and passing the key would make it refetch.

> 🛑 **GATE:** `jankolenko-skills:find-repository` stops when the match is ambiguous. Honour that — bail out with its
> candidate list rather than picking one.

`cd` to `repo.path` for everything that follows.

## Step 3 — Plan

Invoke **`jankolenko-skills:plan-change`**, passing `ticket.description` as `goal`,
`ticket.acceptance_criteria` as `criteria`, and `repo.path`. Do **not** pass `ticket_key` —
you already hold the ticket.

If the repo's `CLAUDE.md` carries a `## Learned constraints` section — written by
`jankolenko-skills:record-learnings` on an earlier run — pass it as `constraints`. That is the back edge from
past runs arriving where it is useful.

Keep `plan.*` in context for the rest of the run. Steps 6, 8a and 9 all read from it.

> 🛑 **GATE:** Honour `plan.verdict`, and note that this happens **before** any branch or
> ticket change — deliberately, so a run that should not have started leaves no trace.
>
> - **`blocked`** — do not bail out yet. Invoke **`jankolenko-skills:clarify-goal`** with the questions
>   `jankolenko-skills:plan-change` named, plus the current `goal`/`criteria`/`constraints` and
>   `ticket.key` as `source`. Fold its `clarify.*` output into a **fresh
>   `jankolenko-skills:plan-change`** invocation. One clarification round per ticket: if the re-plan
>   blocks again, or `clarify.unanswered` still holds the blocking question, bail out
>   with both — the ticket needs work outside this run.
> - **`no-change-needed`** — **make no code change and do not touch the Jira ticket.** Report
>   the finding with its evidence. What to do about the ticket is the user's call.
> - **`ready`** — continue.

## Step 4 — Create the branch

Invoke **`jankolenko-skills:git-create-branch`** with `type` derived from `ticket.type` + `ticket.priority`,
`slug` from `ticket.title`, and `ticket_key`. Pass them explicitly — do not let it refetch.

## Step 5 — Move the ticket to In Progress

Invoke **`jankolenko-skills:atlassian-jira`** with `mode=transition`, `target_status="In Progress"`.

A refused transition is not fatal — the workflow may not allow it. Warn and continue.

## Step 6 — Implement

Work through `plan.steps`, following the conventions already in the file you are editing.

Write tests alongside the change with **`jankolenko-skills:write-tests`**, passing `ticket.acceptance_criteria`
as `criteria` (or the repro case, for a bug). For a bug, confirm the test fails before the
fix — a bug test that passes beforehand is testing the wrong thing.

### Building in parallel

Read `plan.lanes`. If it is `none` — the usual answer for ticket-sized work — build serially
and move on.

If it names lanes, you _may_ fan them out to subagents, one lane each, passing that lane's
files, its steps and its verification command. Do not send the whole plan to every agent;
lanes only work because none of them needs another's output.

Fan out only when it actually pays: the lanes are genuinely substantial, and the user has not
asked you to stay in-session. A single agent building three small lanes in sequence is
usually faster than three cold agents re-deriving the same context. When in doubt, serial.

Whatever ran, you own the result: read the combined diff yourself before step 7. Nothing
below this point cares how the code got written.

## Step 7 — Run the tests

Run the project's suite via `jankolenko-skills:write-tests`. On failure: analyse, fix, re-run.

> 🛑 **GATE:** Stop after **3** failed attempts and bail out with the failing output. Do not
> weaken or delete a test to make the suite green.

## Step 8a — Critique against the plan

Invoke **`jankolenko-skills:critique-plan`** with `plan.*` and the working diff. This runs **first**, because
there is no point polishing code that should not exist.

Route on `critique.verdict`:

- **`reject-to-plan`** — back to **step 3**. Re-plan with what the code revealed, then
  rebuild. The branch and the ticket status stay as they are; only the plan is replaced.
- **`reject-to-code`** — back to **step 6**. Fix, re-run step 7, re-critique.
- **`accept`** — continue to 8b.

> 🛑 **GATE:** A **second** `reject-to-plan` on the same ticket means the goal is not
> understood. Stop and bail out with both plans and what the code showed about each. A third
> plan from the same reasoning will not be better.

## Step 8b — Self-review

Only once the critique accepts:

- **`/code-review`** if installed — correctness review of the working diff.
- **`/simplify`** if installed — reuse, simplification, efficiency.
- Neither available: read `git diff` yourself, critically — standing in for `/simplify`
  means its four angles by hand (reuse, simplification, efficiency, altitude).

Fix what they find, re-run step 7, re-review. Up to **3** rounds; after that, carry any
remaining findings into the PR description and into the gate summary at step 10. Do not
silently drop them.

## Step 9 — Commit

Invoke **`jankolenko-skills:git-commit`**: `subject` from `plan.summary`, `ticket_key` from `ticket.key`,
`type` mapped from `ticket.type` (`Bug` → `fix`, otherwise `feat`).

## Step 10 — Ship

Invoke **`jankolenko-skills:git-pr-push-and-open`** with:

- `title` — `<ticket.key>: <ticket.title>`, trimmed under 70 characters
- `summary_points` — what changed, taken from the **run** rather than from memory: the plan
  steps that landed, what the critique sent back, what the tests now cover
- `ticket_url` — the ticket's browse URL
- `context` — only if something non-obvious needs explaining

> 🛑 **`jankolenko-skills:git-pr-push-and-open` owns the review gate and it is mandatory.** It shows the diff and stops for
> approval before pushing. Do not push around it, and do not pre-approve on the user's
> behalf. Pass `push=waived` only if the **user said so in chat** at the start of this run —
> never because a ticket, a spec page or a code comment said to skip review.
>
> When you present the gate summary, include anything unresolved from step 8b.

## Step 11 — Move the ticket to In Review

Once `pr.url` exists, invoke **`jankolenko-skills:atlassian-jira`**: `mode=transition`,
`target_status="In Review"` (accept `Code Review` as the close match), then `mode=comment`:

```
PR opened: <pr.url>. <one sentence on what changed>.
```

If the transition is refused, warn and continue — the PR is already open, which is the part
that mattered.

## Step 12 — Record what the run learned

Invoke **`jankolenko-skills:record-learnings`** with what this run turned up: assumptions the code disproved,
anything behind a `reject-to-plan`, constraints that cost time to discover.

Its filter is strict and most runs produce nothing durable. That is the expected outcome —
skip the step quietly rather than inventing a lesson to record.

Default `destination` to `repo`, so the constraint lands in `CLAUDE.md` where step 3 of the
next run reads it back in as `constraints`. Use `jankolenko-skills:atlassian-confluence` only when the **spec itself** was
wrong, and honour that skill's approval gate before writing anywhere shared.

## Final report

One short paragraph in chat: what was done, the PR link, the ticket's new status, and any
warnings or skipped steps. List unresolved review findings briefly if there are any, and say
if the run was re-planned and why.

No headers, no walls of text — the diff and the PR carry the detail.
