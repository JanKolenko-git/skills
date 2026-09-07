---
name: plan-change
description: Turn a goal into a concrete implementation plan grounded in the code — which files change, in what order, what could break, and whether the work splits into independent lanes or has to be built serially. Decides up front when no code change is warranted at all, and weighs more than one approach before committing, so a suggested solution is treated as a candidate rather than a given. Use when the user or another skill (e.g. jankolenko-skills:implement-ticket) needs a plan before implementing, or asks to "plan this", "how would you approach this", or "work out what needs changing".
---

# Plan Change

Read the code, then decide what to do to it. One plan, written down, before anything is
edited.

Everything downstream inherits these decisions — a bad plan executed perfectly is still a bad
result — so this skill is biased toward reading more and committing later.

## Inputs

- `goal` — **required.** What needs to change and why. A ticket description, a bug report, a
  sentence from the user.
- `criteria` — acceptance criteria, or a bug's reproduction case. Sharpens the plan and is
  passed on to `jankolenko-skills:write-tests` later.
- `candidates` — approaches somebody has already proposed, e.g. a ticket's "proposed
  change". They enter Step 3's comparison as entries, never as the decision.
- `constraints` — known constraints from earlier runs (see `jankolenko-skills:record-learnings`), house rules,
  anything already ruled out.
- `repo.path` — optional. Defaults to the current repository.
- `ticket_key` — optional. If given and **`jankolenko-skills:atlassian-jira` is installed**, fetch the ticket for
  `goal` and `criteria`. A caller holding ticket data should pass them directly.

## Output

| Field | Contents |
| --- | --- |
| `plan.verdict` | `ready` / `blocked` / `no-change-needed` |
| `plan.approach` | The approach chosen, the ones rejected, and the fact that decided |
| `plan.summary` | The approach, one paragraph |
| `plan.files` | Each file to touch, with what changes in it |
| `plan.steps` | Ordered steps, each independently checkable |
| `plan.lanes` | Independent lanes the work splits into, or `none` |
| `plan.risks` | What could break, and what would catch it |
| `plan.open_questions` | Unresolved, with what would resolve each |

## Step 1 — Read before planning

A plan written from the ticket alone is a guess. Ground it:

- Grep for the symptoms, the feature name, the error string.
- Read the files that actually matter, not just their names.
- `git log --oneline -15 -- <paths>` — recent work here often explains the shape.
- Check for existing tests around the behaviour; they document the current contract.

If **`mattpocock-skills:codebase-design`** is installed, use it to check the approach against
the module boundaries the codebase already has.

## Step 2 — Decide whether there is anything to build

Before planning a change, rule out that no change is warranted:

- Not a code issue — config in an external tool, a data fix, a process question, a
  third-party dependency.
- Cannot be reproduced, or there is not enough information to act.
- Already fixed in a recent commit, or no longer relevant.

> 🛑 **GATE:** If any of these hold, return `plan.verdict = no-change-needed` with the
> evidence — cite files, commits, or the failed repro. Stop there. What to do about it is the
> caller's decision, not this skill's.

## Step 3 — Weigh a second approach before committing to the first

The approach that arrives with the goal — the ticket's "proposed change", the obvious fix,
the one already in your head — is a **candidate, not the plan**. Name at least one more.

Two is usually enough, and they have to differ in mechanism: if the only difference is a
constant, that is one approach and a tuning question, not two.

Compare them on what actually decides it:

- **Does it solve the whole problem**, or the symptom noticed first?
- **What does it assume?** An approach resting on an unmeasured assumption is a guess in a
  plan's clothing. Where the assumption is cheap to check, check it now; where it is not, it
  belongs in `plan.risks` with its detector.
- **What breaks it later** — a caller you have not met, an environment that behaves
  differently, a value someone retunes.

Then take the **simplest approach that fully solves it**, in that order. Simple and
predictable is usually right, and an approach that fits in your head is one the next person
can debug — but simplicity breaks ties between approaches that work, it never excuses one
that half-works.

Record it in `plan.approach`: what you chose, what you rejected, and the fact that decided
between them. A reader who disagrees needs the alternative to argue with.

> 🛑 **GATE:** If the only approach you can name is the one the goal arrived with, say so in
> `plan.approach`, and why nothing else fits. That is a fair answer for a small change — but
> writing it down is what stops "the ticket said so" from passing as a decision.

## Step 4 — Write the plan

Name real paths and real functions. "Update the cart logic" is not a plan; "add VAT rounding
in `cart/totals.ts:calcTax`, and widen the fixture in `cart/totals.test.ts`" is.

For each step, state what would show it worked. A step nobody can check is a step nobody can
reject.

In `plan.risks`, pair each risk with its detector — the test, the log line, the manual check.
A risk with nothing that would catch it is an open question, not a risk.

> 🛑 **GATE:** If the goal is too vague to name files and steps, return
> `plan.verdict = blocked` with the **specific** question that would unblock it. Do not write
> a plausible-sounding plan over a gap.

## Step 5 — Partition into lanes, or refuse to

Only then, ask whether the work splits. A lane split is real only if **all four** hold:

1. **No file appears in two lanes.** Not "rarely conflicts" — none.
2. **No lane reads another's output.** If lane B needs a type, helper or endpoint that lane A
   introduces, they are one lane.
3. **Each lane is verifiable alone** — its own tests pass without the others landing.
4. **Each lane is substantial.** Splitting a two-file change is overhead, not parallelism.

If all four hold, list the lanes with their files and their verification command. Otherwise
set `plan.lanes = none` and say which condition failed.

`none` is the common and correct answer for ticket-sized work. Reaching for lanes that do not
exist costs a merge, a re-read and a coherence pass to save nothing — the caller decides
whether to fan out, and it can only decide honestly if this field is honest.

## Notes

- The plan is a document, not a commitment. When the code contradicts it mid-build, say so
  and revise — `jankolenko-skills:critique-plan` exists to catch exactly that, and re-planning is cheaper than
  defending a plan you no longer believe.
- Do not start editing. This skill produces a plan; something else builds it.
