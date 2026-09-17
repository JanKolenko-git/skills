---
name: test
description: Write tests in the repository's own runner, layout and style, covering the acceptance criteria or the bug's repro, not internals; the uncommitted diff is the default target; stops before adding a framework the repo lacks. Use when the user asks to write, add, update or extend tests, add coverage, or test a fix. Test-first is mattpocock-skills:tdd.
---

# Test

Write tests that look like they were always there, same runner, same layout, same idioms,
covering what the change is supposed to *do*. Ordering-agnostic: it works before the
implementation or after it and imposes no red-green-refactor; that discipline is
`mattpocock-skills:tdd`.

## Inputs

- `target` — what to cover: changed files, a function, a described behaviour. Defaults to
  the uncommitted diff, `git diff --name-only HEAD` plus untracked files, with tests,
  config, lockfiles, styles and generated output left out.
- `criteria` — the acceptance criteria, or the bug's reproduction case. Without this, tests
  end up asserting whatever the code happens to do. A caller holding a ticket passes them
  from it; this skill fetches nothing.

## Output

| Field | Contents |
| --- | --- |
| `tests.files` | Test files created or modified |
| `tests.command` | The exact command that runs them |
| `tests.result` | `pass` / `fail`, with the failing output if it failed |
| `tests.uncovered` | Criteria you could not express as a test, and why |

## Step 1 — Learn the conventions before writing anything

Never introduce a second testing style into a repo. The runner comes from `package.json`
scripts and devDependencies, then `pyproject.toml`, `Cargo.toml`, `go.mod`, a `Makefile`;
the location (co-located `*.test.ts` or a `tests/` tree) and the style (naming, fixtures or
factories, mocking, table-driven cases) from two or three neighbouring test files.

```bash
ls **/*.test.* **/*_test.* tests/ 2>/dev/null | head -20
```

> 🛑 **GATE — no test suite.** The repository has no runner, no test files, no test config.
> Ask through `AskUserQuestion`: "This repository has no test suite; which runner should it
> adopt?" — one option per plausible runner for the stack, plus **stop**.
> Standing up a framework, its config and its CI wiring is a project decision, not a side
> effect of a ticket. Standing rule: refuse rather than guess.

## Step 2 — Pick the strategy by what each file is

| File | Strategy |
| --- | --- |
| Plain logic: utilities, hooks, services, domain code | Unit: inputs to outputs, edge cases, error paths |
| A component, page or view | Render, interact, assert on the DOM and its accessibility tree |
| A route, handler, controller or resolver | Integration: call it, mock at the boundary, assert the response shape |
| A CLI entry point | Invoke the command, assert stdout, stderr and the exit code |
| A flow the change alters end to end | One end-to-end case, only with a runner the repository already has |

Done when: every file in `target` has a strategy, or a reason it is not tested (framework
internals, third-party code, generated files).

## Step 3 — Cover behaviour, not implementation

For a bug, write the test that reproduces it first and confirm it fails for the stated
reason; a bug test that passes before the fix tests the wrong thing. For a feature, one
test per acceptance criterion, named after the criterion so a failure reads as a
requirement that broke, plus the edge cases the ticket names: empty, null, boundary, error
paths. Assert on public behaviour and observable output; tests that reach into private
state break on every refactor and protect nothing.

A test leaves the environment as it found it: a listener on a shared `document`, a
redefined global, an env var, a monkeypatch, a temp file, a row is consumed or restored
before the test returns. Module-level resets are the usual false comfort: `vi.resetModules`
resets your module, not the environment it touched. The tell is a test that passes alone
and fails once the file is reordered.

## Step 4 — Run them

Run the narrow suite (the file or directory) while iterating, then the full suite once
before reporting, with the project's own command. Report `tests.result` honestly; "tests
pass" when they do not is worse than no tests. A criterion that cannot be tested (a live
service, a device, a browser you cannot drive) goes in `tests.uncovered` rather than into a
hollow test that asserts nothing.

Done when: every criterion has a test or a row in `tests.uncovered`, and `tests.result`
reflects the last full run.
