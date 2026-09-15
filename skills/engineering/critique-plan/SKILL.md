---
name: critique-plan
description: Review a diff against the plan it was meant to implement: what the plan asked for that never landed, what the diff does that no step asked for, whether the plan still holds now the code exists. Use when the user asks whether the implementation matches the plan or the ticket's intent, whether something is in scope, or whether a change should exist.
context: fork
---

# Critique Plan

Tests ask *does it run*; `/code-review` asks *is it correct*; this skill asks *should it
exist*: does the diff match the intent it came from. It runs in a fresh context, on
purpose, so the critic does not share the implementer's reasoning.

## Inputs

- `plan` — **required.** The `plan.*` fields from `jankolenko-skills:plan-change`, or any
  written plan, passed in full in the invocation: this skill cannot see the caller's
  context. Without a plan there is nothing to critique against; ask for one rather than
  inventing it.
- `diff` — optional. Defaults to the working diff against the base branch.
- `criteria` — optional. Acceptance criteria, checked in question 1.

## Output

| Field | Contents |
| --- | --- |
| `critique.verdict` | `accept` / `reject-to-plan` / `reject-to-code` |
| `critique.missing` | Plan steps or criteria with no corresponding change |
| `critique.unplanned` | Changes no plan step asked for |
| `critique.findings` | Each finding: what, where, which question it fails |

Not bugs, style, naming, performance or test quality: those belong to `/code-review` and
`/simplify`, and duplicating them buries the one signal this skill produces. An unmissable
bug gets one line and is handed on.

## Step 1 — Establish what changed

```bash
git diff --stat <base>...HEAD && git diff <base>...HEAD
```

Read the whole diff; a critique built from the file list cannot answer question 2.

## Step 2 — Ask the four questions

1. **Did it build what the plan said?** Walk `plan.steps` and `criteria` one at a time and
   find the change that implements each. A step with nothing behind it, or half of it, goes
   in `critique.missing` with which half.
2. **Is there anything the plan did not ask for?** Walk the diff hunk by hunk and map each
   back to a step. Anything unmapped goes in `critique.unplanned`: drive-by refactors,
   renames, a second bug fixed, a dependency added, config touched. Unplanned is undeclared
   and unreviewed against any intent; each either earns a plan step or leaves the diff.
3. **Should it exist at all?** Now that the code is real: was this the right approach, does
   the change sit where it belongs, did building it surface something that makes the plan
   look wrong? A faithful implementation of the wrong idea is the failure this seat exists
   to catch.
4. **Does it hold under the plan's premise?** For each condition the plan named (a device,
   a load, a caller, a failure mode), find the line that meets it and the test that
   exercises it. A test that reaches for a convenient stand-in verifies the plan's shape,
   not its premise: fake timers never block, so they cannot show what a blocked main thread
   does. A premise nothing exercises is a finding, not a pass.

## Step 3 — Route the verdict

By where the fix has to happen, not by how many findings there are: `accept` when the diff
implements the plan, nothing is undeclared and the approach holds (residual concerns noted,
not blocking); `reject-to-code` when the plan is right and the code does not match it yet,
the ordinary case; `reject-to-plan` when the plan itself is wrong and building it more
faithfully makes things worse, with what the plan got wrong and what the code revealed. A
second `reject-to-plan` on the same work is the signal to stop and put the question to the
user: two failed plans mean the goal is not understood.

## Notes

- Critique the work, not the worker, and never soften a verdict because the diff represents
  effort. A rejection here is cheap; the same rejection in review is not.
- A plan written after the code agrees with it by construction; say so, since this skill
  can then tell you nothing.
