---
name: critique-plan
description: Review a diff against the plan it was meant to implement — what the plan asked for and the diff never did, what the diff does that no plan step asked for, and whether the plan still looks right now the code exists. Routes rejections back to the plan or back to the code. Use when the user or another skill (e.g. jankolenko-skills:implement-ticket) has implemented a plan and wants it checked against intent rather than for bugs, or asks "does this match the plan", "is this in scope", or "should this exist".
---

# Critique Plan

Tests ask *does it run*. `/code-review` asks *is it correct*. This skill asks *should it
exist* — does the diff in front of you match the intent it came from.

## Inputs

- `plan` — **required.** The `plan.*` fields from `jankolenko-skills:plan-change`, or any written plan. Without
  a plan there is nothing to critique against; ask for one rather than inventing it.
- `diff` — optional. Defaults to the working diff against the base branch.
- `criteria` — optional. Acceptance criteria, checked as part of question 1.

## Output

| Field | Contents |
| --- | --- |
| `critique.verdict` | `accept` / `reject-to-plan` / `reject-to-code` |
| `critique.missing` | Plan steps or criteria with no corresponding change |
| `critique.unplanned` | Changes no plan step asked for |
| `critique.findings` | Each finding: what, where, and which question it fails |

## Scope — what this skill does not do

Not bugs, not style, not naming, not performance, not test quality. Those belong to
`/code-review` and `/simplify`, and duplicating them here wastes a pass and buries the one
signal this skill exists to produce.

If a correctness bug is unmissable, note it in a single line and hand it on. Do not expand
into a code review.

## Step 1 — Establish what actually changed

```bash
git diff --stat <base>...HEAD
git diff <base>...HEAD
```

Read the whole diff. A critique built from the file list alone cannot answer question 2.

## Step 2 — Ask the three questions

**1. Did it build what the plan said?**
Walk `plan.steps` and `criteria` one at a time and find the change that implements each. A
step with nothing behind it goes in `critique.missing`. Half-implemented counts as missing —
say which half.

**2. Is there anything here the plan did not ask for?**
Walk the diff the other way, hunk by hunk, and map each back to a step. Anything unmapped
goes in `critique.unplanned`: drive-by refactors, opportunistic renames, a second bug fixed
along the way, a dependency added, config touched.

Unplanned is not automatically wrong — but it is automatically *undeclared*, and it has not
been reviewed against any intent. Each one either earns a plan step retroactively or comes
out of the diff.

**3. Should it exist at all?**
The question the other two cannot reach. Now that the code is real: was this the right
approach? Does the change sit where it belongs, or has it been bolted to the first file that
would accept it? Did implementing it surface something that makes the plan look wrong?

Approving a faithful implementation of the wrong idea is the failure mode this seat exists to
prevent.

## Step 3 — Route the verdict

Route by **where the fix has to happen**, not by how many findings there are:

- **`accept`** — the diff implements the plan, nothing undeclared, the approach still holds.
  Note any residual concerns without blocking.
- **`reject-to-code`** — the plan is still right; the code does not match it yet. Findings go
  back to whoever is implementing. This is the ordinary case.
- **`reject-to-plan`** — the plan itself is wrong, and building it more faithfully makes
  things worse. Goes back to `jankolenko-skills:plan-change`, not to the implementer. Say what the plan got
  wrong and what the code revealed.

> 🛑 **GATE:** One `reject-to-plan` is a re-plan; a second on the same work is a signal to
> stop and put the question to the user. Two failed plans mean the goal is not understood,
> and a third plan written by the same reasoning will not fix that.

## Notes

- Critique the work, not the worker — and never soften a verdict because the diff represents
  effort. A rejection here is cheap; the same rejection in review is not.
- If the plan was written after the code, say so. A plan reverse-engineered from a diff
  agrees with it by construction and this skill cannot tell you anything.
