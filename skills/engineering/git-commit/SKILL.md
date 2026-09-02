---
name: git-commit
description: Stage and commit the current work with a conventional message — type, an optional ticket key, and a concise subject line — reviewing the diff first and never committing unrelated or secret-bearing files. Use when the user or another skill (e.g. jankolenko-skills:implement-ticket) wants changes committed locally, or asks to "commit this" or "commit with a ticket reference". Committing only; it does not push.
---

# Git Commit

Stage and commit the current change with a message that says what happened.

**Local only.** This skill never pushes and never opens a PR — a commit is reversible, which
is why it needs no confirmation gate. Pushing is not, and lives in `jankolenko-skills:git-pr-push-and-open`.

## Inputs

- `subject` — **required.** One line, imperative, what the change does.
- `type` — `feat` | `fix` | `chore` | `refactor` | `test` | `docs`. Inferred from the change
  if omitted.
- `ticket_key` — optional. Included in the message when present.
- `files` — optional. Specific paths to stage. Defaults to the files this session changed —
  **never** a blanket `git add -A`.

## Output

| Field | Contents |
| --- | --- |
| `commit.sha` | Short SHA of the new commit |
| `commit.message` | The full message used |
| `commit.files` | What was staged |

## Step 1 — Look at what you are about to commit

```bash
git rev-parse --abbrev-ref HEAD
git status --short
git diff
git diff --staged
```

Three things to catch before staging:

- **The wrong branch.** The branch you are on is the one that happened to be checked out,
  not necessarily the one this work belongs to. Committing onto a colleague's feature
  branch puts your change inside their open PR, where they will not expect it and cannot
  easily remove it. Check the branch matches the work *before* staging — `jankolenko-skills:git-create-branch`
  makes the right one if it does not.
- **Unrelated changes.** Debug logging, a stray formatting sweep, an editor config. Leave
  them out — a commit that mixes a fix with 200 lines of reformatting is unreviewable.
- **Secrets.** `.env`, tokens, keys, credentials in fixtures. Stop and tell the user rather
  than committing them; a secret in git history is not fixed by a follow-up commit.

Stage explicitly, by path:

```bash
git add <path> <path>
```

## Step 2 — Adopt the repository's convention

Check what this repo enforces **before** composing the message. A rejected commit wastes a
round trip, and a repo's rule always wins over the default below.

```bash
git config core.hooksPath           # often .githooks
ls .githooks/ .husky/ 2>/dev/null
ls commitlint.config.* .commitlintrc* 2>/dev/null
git log -10 --format=%s             # what the history actually looks like
```

If you find a validator (a `commit-msg` hook, `commitlint`, a `verify-commit-msg` script),
**read it** — the allowed types and the subject rules are usually literal values in it — and
follow that. Some repos restrict the type list, cap the subject length, or require the ticket
in the footer rather than the subject.

## Step 3 — Write the message

Default, when the repo has no rule of its own — [Conventional
Commits](https://www.conventionalcommits.org):

```
<type>(<scope>): <subject>

<body, only when the why is not obvious>

Refs: <TICKET-KEY>
```

- The **colon is required**, and `<scope>` is the area of the codebase (`gate`, `auth`,
  `cart`) — lowercase. It is **not** the ticket key: many validators restrict scope to
  `[a-z0-9._-]+`, so an uppercase key like `PROJ-1234` is rejected there.
- Put the ticket in a `Refs:` footer, which is where tooling looks for it.
- Subject imperative and under ~70 characters: "fix VAT rounding on cart total", not "fixed"
  or "this fixes".
- Say **what changed**, not which files changed — the diff already lists those.
- Body only when the *why* is not evident from the diff: the constraint you worked around,
  the approach you rejected. Wrap at 72.

```
fix(cart): correct VAT rounding on totals

Totals rounded per line item before summing, so a 3-item cart drifted by
up to 2 cents. Round once on the total instead.

Refs: PROJ-1234
```

If the repo's own history plainly puts the ticket in the subject, match the history instead —
consistency inside one repo beats the general convention.

## Step 4 — Commit

```bash
git commit -m "<message>"
```

Report the short SHA.

Do **not** add co-author trailers, tool attribution, or emoji unless the repository's own
history already uses them — check `git log -10 --format=%B` and match what is there.

> 🛑 If a commit hook rejects the commit, surface the hook's output and stop. Do not retry
> with `--no-verify`. The hook is the project's rule, not an obstacle.
