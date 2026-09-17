---
name: debug
description: Find and fix a bug's root cause through a diagnosis loop: a feedback loop that goes red on the exact symptom, reproduce and minimise, rank hypotheses, instrument one variable at a time, fix at the root with a regression test. Use when the user says debug or diagnose this, or reports something broken, throwing, failing, flaky or slow.
---

# Debug

A bug is found by a loop, not by reading code for a theory. One command that goes red on
this symptom and green once it is fixed is most of the work; bisection, hypotheses and
instrumentation only consume it.

## Inputs

- `symptom` — **required.** What is observed, what was expected, and how it is triggered:
  the error, the wrong output, the timing, the steps.
- `repro` — optional. A test, command, request or recording that already shows it.
- `constraints` — optional. Environments you may touch, what is already ruled out.

## Output

| Field | Contents |
| --- | --- |
| `bug.loop` | The one command that goes red on the symptom, with its output |
| `bug.cause` | The confirmed hypothesis and the evidence that confirmed it |
| `bug.fix` | Files changed, and why the change addresses the cause |
| `bug.test` | The regression test, or why no correct seam exists |
| `bug.siblings` | Other places the same cause was found, fixed or noted |

Redact before showing any command, output or captured artefact: `<REDACTED>` in place of
every secret, loops built against env vars, only the lines that carry the signal quoted.
Standing rule: no secrets in output.

## Step 1 — Pin the symptom

Write down observed, expected and trigger before touching code; read `CONTEXT.md` and the
area's ADRs when they exist. A symptom you cannot state precisely has no loop; ask for the
exact steps, inputs and environment rather than guess. Done when: observed,
expected and trigger are three concrete lines.

## Step 2 — Build a feedback loop that goes red

Spend the effort here. In rough order of preference: a failing test at the seam that
reaches the bug; a request against a running dev server; a CLI run diffed against known-good
output; a headless-browser script asserting on DOM, console or network; a captured trace
replayed through the code path; a throwaway harness around one function; a loop of random
inputs for a "sometimes wrong" bug; a bisection harness for `git bisect run`; a differential
run of two versions; last, a human driving the steps through
`${CLAUDE_SKILL_DIR}/scripts/hitl-loop.template.sh`.

Then tighten it: faster (skip unrelated setup), sharper (assert the symptom, not "did not
crash"), deterministic (pin time, seed randomness, freeze the network). A flaky bug gets a
higher reproduction rate: loop the trigger, add stress, narrow the timing window until it
fails often enough to debug against.

Done when: one command, already run once with its redacted output shown, drives the real
code path, asserts the user's exact symptom, gives the same verdict every run, finishes in
seconds and runs unattended. No such command: stop, list what was tried, and ask for an
environment, a redacted artefact or permission to instrument. No loop, no Step 3.

## Step 3 — Reproduce and minimise

Run the loop and watch it go red on the failure the user described, not a neighbour of it.
Then remove inputs, callers, config, data and steps one at a time, re-running after each
cut, until every remaining element is load-bearing. Done when: removing any one element
turns the loop green.

## Step 4 — Rank the hypotheses

Write three to five falsifiable hypotheses before testing any, each with its prediction:
"if X is the cause, changing Y makes the bug disappear." Root cause, not symptom: "the value
is null here" is what you saw; why it is null is the hypothesis. Show the ranked list to the
user and continue; they often re-rank it. When the bug appeared between two known states,
bisect history first. Done when: each hypothesis names the experiment that would refute it.

## Step 5 — Instrument one variable at a time

A breakpoint beats ten logs; targeted logs at the boundaries that separate two hypotheses
beat logging everything. Tag every log with one prefix, `[DEBUG-a4f2]`, so cleanup is one
grep. For a performance regression, measure a baseline first and bisect on the number. A refuted hypothesis is discarded with its change; a
confirmed one is the cause. Done when: `bug.cause` names the evidence.

## Step 6 — Fix at the root, with a test

Write the regression test before the fix, at a seam that exercises the bug pattern as it
occurs at the call site; a seam too shallow to reproduce the chain gives false confidence,
and no correct seam is itself a finding. Watch it fail, apply the smallest change that
addresses the cause, watch it pass, re-run the Step 2 loop on the original scenario. Grep
for siblings: the same cause usually hides behind the same pattern elsewhere. A cause that
is a design decision rather than a coding mistake is routed to `jankolenko-skills:architect`. Done when: the loop is green on the un-minimised
scenario, and `bug.test` exists or its absence is explained.

## Step 7 — Clean up

Done when: the original repro no longer reproduces, the regression test passes, a grep for
the tag finds no instrumentation, throwaway harnesses are deleted, and the confirmed
hypothesis is stated in the commit message for the next debugger.

## Notes

- The diff carries the fix and its test; a feature or a refactor is a separate change.
- Writing the wider suite around the fix is `jankolenko-skills:test`.
