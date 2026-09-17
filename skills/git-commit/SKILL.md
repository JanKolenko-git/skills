---
name: git-commit
description: Stage and commit the work with a conventional message: reviews the diff first, stages by path, keeps unrelated changes and secrets out, follows the repository's commit rules. Use for every commit, including 'commit and push', 'commit this' and 'commit to the branch', rather than committing through git directly. Pushing is git-pr-push-and-open.
allowed-tools: Bash(git status*), Bash(git diff*), Bash(git log*), Bash(git rev-parse*), Bash(git config core.hooksPath), Bash(git add *), Bash(git commit *)
---

# Git Commit

Stage and commit the current change with a message that says what happened. Local only: a
commit is reversible, so it needs no gate; pushing is not, and lives in
`jankolenko-skills:git-pr-push-and-open`.

## Inputs

- `subject` — **required.** One line, imperative, what the change does.
- `type` — `feat` | `fix` | `chore` | `refactor` | `test` | `docs`. Inferred if omitted.
- `ticket_key` — optional. Goes in the message when present.
- `files` — optional. Paths to stage. Defaults to the files this session changed, never a
  blanket `git add -A`.

## Output

| Field | Contents |
| --- | --- |
| `commit.sha` | Short SHA of the new commit |
| `commit.message` | The full message used |
| `commit.files` | What was staged |

## Step 1 — Look before staging

```bash
git rev-parse --abbrev-ref HEAD && git status --short && git diff && git diff --staged
```

- **The wrong branch.** A commit onto a colleague's feature branch lands inside their open
  PR; `jankolenko-skills:git-create-branch` makes the right one first.
- **Unrelated changes.** Debug logging, a formatting sweep, an editor config: leave them
  out. A fix mixed with 200 lines of reformatting is unreviewable.
- **Secrets.** `.env`, tokens, keys, credentials in fixtures: stop and tell the user. A
  secret in git history is not fixed by a follow-up commit.

Then stage by path: `git add <path> <path>`.

## Step 2 — Adopt the repository's convention

```bash
git config core.hooksPath; ls .githooks/ .husky/ commitlint.config.* .commitlintrc* 2>/dev/null
git log -10 --format=%s
```

A validator (a `commit-msg` hook, `commitlint`, a `verify-commit-msg` script) holds the
allowed types and subject rules as literal values: read it and follow it. The repo's rule
wins over the default below; if its history puts the ticket in the subject, match the
history.

## Step 3 — Write the message

Default, [Conventional Commits](https://www.conventionalcommits.org):

```
<type>(<scope>): <subject>

<body, only when the why is not obvious from the diff>

Refs: <TICKET-KEY>
```

The colon is required; `<scope>` is a lowercase area of the codebase (`cart`, `auth`), never
the ticket key, which validators restricting scope to `[a-z0-9._-]+` reject. Subject
imperative, under 70 characters, what changed rather than which files; body wrapped at 72,
only for the constraint worked around or the approach rejected.

```
fix(cart): correct VAT rounding on totals

Totals rounded per line item before summing, so a 3-item cart drifted by
up to 2 cents. Round once on the total instead.

Refs: PROJ-1234
```

## Step 4 — Commit

`git commit -m "<message>"`, then report the short SHA. No co-author trailers, tool
attribution or emoji unless `git log -10 --format=%B` shows the repository already uses
them. If a hook rejects the commit, surface its output and stop; the hook is the project's
rule, so never retry with `--no-verify`.
