---
name: check
description: Confirm a change does what it was meant to and breaks nothing else: the diff against its plan or ticket, the changed behaviour run for evidence, the same surfaces compared with the base branch. Use when the user asks whether the implementation matches the plan, whether it works or regresses anything, or before a PR. Bugs are /code-review.
context: fork
---

# Check

Tests ask *does it run*; `/code-review` asks *is it correct*; this skill asks *should it
exist, and does it hold*: does the diff match the intent it came from, does it behave when
run, and does everything it touches still behave as the base branch does. It runs in a
fresh context, on purpose, so the judge does not share the builder's reasoning.

## Inputs

- `plan` — the `plan.*` fields from `jankolenko-skills:plan`, or any written plan, passed in
  full: this skill cannot see the caller's context. Without one, Step 2 judges against
  `criteria` and says so; with neither, ask for one rather than inventing it.
- `criteria` — acceptance criteria, or the bug's reproduction.
- `diff` — optional. Defaults to the branch and working tree against `base`.
- `base` — optional. Defaults to the default branch, `origin/<default>` when there is a remote.
- `run` — optional. How to start the app when the repository does not document it.

## Output

| Field | Contents |
| --- | --- |
| `check.verdict` | `accept` / `reject-to-plan` / `reject-to-code` / `blocked` |
| `check.missing` | Plan steps or criteria with no corresponding change |
| `check.unplanned` | Changes no plan step asked for |
| `check.evidence` | Per behaviour: the command or URL, what it returned, `pass` / `fail` / `blocked` |
| `check.regressions` | Surfaces that behave differently from `base` where the plan asked for no difference |
| `check.findings` | Each finding: what, where, which question it fails |

Not bugs, style, naming, performance or test quality: those belong to `/code-review` and
`/simplify`. An unmissable bug gets one line and is handed on.

## Step 1 — Establish what changed

```bash
git fetch -q origin 2>/dev/null; git diff --stat <base>...HEAD && git diff <base>...HEAD
```

Read the whole diff; a critique built from the file list cannot answer question 2. Compare
with the fetched base: a local branch that fell behind measures against history nobody will
merge into. Done when: every hunk has been read.

## Step 2 — Ask the four questions of intent

1. **Did it build what the plan said?** Walk `plan.steps` and `criteria` one at a time and
   find the change that implements each. A step with nothing behind it, or half of it, goes
   in `check.missing` with which half.
2. **Is there anything the plan did not ask for?** Walk the diff hunk by hunk and map each
   back to a step. Anything unmapped goes in `check.unplanned`: drive-by refactors,
   renames, a second bug fixed, a dependency added, config touched. Unplanned is undeclared
   and unreviewed against any intent; each either earns a plan step or leaves the diff.
3. **Should each part exist?** Now that the code is real, ask it of every part of the diff,
   not once of the whole: does the part's win, priced in the plan or measured here, pay for
   its code; does it sit where it belongs; did building it surface something that makes the
   plan look wrong? Code outside the feature that grew to serve it is the tell. A faithful
   implementation of the wrong idea is the failure this seat exists to catch.
4. **Does it hold under the plan's premise?** For each condition the plan named (a device,
   a load, a caller, a failure mode), find the line that meets it and the test that
   exercises it. A test that reaches for a convenient stand-in verifies the plan's shape,
   not its premise: fake timers never block, so they cannot show what a blocked main thread
   does. A premise nothing exercises is a finding, not a pass.

Done when: every step and criterion has a matching change or a row in `check.missing`, and
every hunk maps to a step or a row in `check.unplanned`.

## Step 3 — Run it and keep the evidence

Run the suite with the repository's own command, then exercise each behaviour the change
adds or alters the way a caller reaches it: the request and its body for an API, the route
and what rendered for a page, the command and its output for a CLI. Start the app the way
the repository documents, else as `run` says; when neither is known, the behaviour is
`blocked` with what would unblock it. Record each observation in `check.evidence` as you
make it.

No evidence, no pass: a behaviour reasoned about from the code is `blocked`, however sure
you are, and a run in which nothing started passes nothing. Done when: every behaviour has
a row with the command or URL, the observation and a verdict.

## Step 4 — Compare with the base

For each surface the change touches that the plan asked to leave alone, an endpoint, a
page, a query, a command, a build artefact, capture the same observation on `base` and diff
the two. A throwaway worktree keeps the comparison honest; a stash leaves new files behind.

```bash
git worktree add -q /tmp/check-base <base> && (cd /tmp/check-base && <install, build, observe>); git worktree remove --force /tmp/check-base
```

A difference the plan did not ask for is a row in `check.regressions` with both outputs.
Skip the step, and say so, when the change touches nothing shared or `base` cannot be built
here. Done when: every shared surface is identical, a regression, or named as skipped.

## Step 5 — Route the verdict

By where the fix has to happen: `accept` when the diff implements the plan, nothing is
undeclared, every behaviour has evidence and no regression is listed; `reject-to-code` when the plan is right and the code,
its behaviour or a shared surface does not match it yet, the ordinary case; `reject-to-plan`
when the plan itself is wrong and building it more faithfully makes things worse, with what
the plan got wrong and what the code revealed; `blocked` when nothing could be exercised,
with what would unblock it. A second `reject-to-plan` on the same work means the goal is
not understood: stop and put the question to the user.

## Notes

- Critique the work, not the worker; a rejection here is cheap, the same one in review is not.
- A plan written after the code agrees with it by construction; say so.
- Reports only. A failing behaviour goes to `jankolenko-skills:debug`, a missing one to the
  builder; nothing here edits code.
