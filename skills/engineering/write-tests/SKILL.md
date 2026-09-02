---
name: write-tests
description: Write tests for a change against the conventions the repository already uses — detecting the runner, matching existing file layout and assertion style, and covering the acceptance criteria or bug repro rather than the implementation's internals. Use when the user or another skill (e.g. jankolenko-skills:implement-ticket) needs tests for new or changed code, or asks to "write tests", "add test coverage", or "test this fix".
---

# Write Tests

Write tests that look like they were always there — same runner, same layout, same idioms —
covering what the change is supposed to *do*.

This skill is deliberately **ordering-agnostic**: it works before the implementation
(test-first) or after it. It does not impose red-green-refactor. If you want TDD's discipline
specifically, use a TDD skill instead; this one slots into an existing flow.

## Inputs

- `target` — **required.** What to cover: changed files, a function, a described behaviour.
- `criteria` — the acceptance criteria, or the bug's reproduction case. Without this, tests
  end up asserting whatever the code happens to do.
- `ticket_key` — optional. If given and **`jankolenko-skills:atlassian-jira` is installed**, pull the acceptance
  criteria from the ticket. Callers holding ticket data should pass `criteria` directly.

## Output

| Field | Contents |
| --- | --- |
| `tests.files` | Test files created or modified |
| `tests.command` | The exact command that runs them |
| `tests.result` | `pass` / `fail`, with the failing output if it failed |
| `tests.uncovered` | Criteria you could not express as a test, and why |

## Step 1 — Learn the conventions before writing anything

Never introduce a second testing style into a repo. Establish:

- **Runner** — check `package.json` scripts and devDependencies, then `pyproject.toml`,
  `Cargo.toml`, `go.mod`, a `Makefile`. Vitest, Jest, pytest, `go test`, JUnit — whatever is
  already there.
- **Location** — co-located `*.test.ts` beside the source, or a separate `tests/` tree? Copy
  the existing choice.
- **Style** — read two or three neighbouring test files. Note how they name cases, whether
  they use fixtures or factories, how they mock, whether they favour table-driven cases.

```bash
ls **/*.test.* **/*_test.* tests/ 2>/dev/null | head -20
```

> 🛑 **GATE:** If there is no test suite at all, **STOP** and ask before creating one.
> Standing up a test framework is a project decision — the runner, the config, the CI wiring
> — not a side effect of fixing a ticket.

## Step 2 — Cover behaviour, not implementation

- For a **bug**: write the test that reproduces it first, and confirm it fails for the stated
  reason. A bug test that passes before the fix is testing the wrong thing.
- For a **feature**: one test per acceptance criterion, named after the criterion so a
  failure reads as a requirement that broke.
- Cover the edge cases the ticket names — empty, null, boundary, error paths.

Assert on public behaviour and observable output. Tests that reach into private state break
on every refactor and protect nothing.

Do not test framework internals, third-party libraries, or generated code.

## Step 3 — Run them

```bash
<the project's own test command>
```

Run the **narrow** suite while iterating (the file or the directory), then the full suite
once before reporting. Report `tests.result` honestly — a skill that says "tests pass" when
they do not is worse than no tests.

If a test cannot be written for a criterion — it needs a live service, a device, a browser
you cannot drive — say so in `tests.uncovered` rather than writing a hollow test that asserts
nothing.
