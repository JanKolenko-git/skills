---
name: git-create-branch
description: Create a branch named the way the repository names branches, from a clean default branch: its own convention if stated, else feature/, bugfix/ or hotfix/ plus ticket key and slug. Use when the user asks for a branch, starts work on a ticket, or is about to change code with no branch yet.
---

# Git Create Branch

Create a well-named branch off the default branch, so the name says what the work is and
which ticket it answers.

## Inputs

- `type` — `feature` | `bugfix` | `hotfix`. Derived from the ticket's type and priority if
  omitted (Step 1).
- `slug` — 3–5 words describing the work, kebab-cased. Derived from the title if omitted.
- `ticket_key` — optional. Goes into the name; a caller holding the ticket passes the key,
  `type` and `slug` from it, and this skill fetches nothing.
- `base` — optional. Defaults to the repository's default branch.

## Output

| Field | Contents |
| --- | --- |
| `branch.name` | The branch created, e.g. `bugfix/PROJ-1234-cart-vat-rounding` |
| `branch.base` | What it was branched from |
| `branch.existed` | `true` if the branch already existed and was checked out instead |

## Step 1 — Resolve the type

| Issue type | Priority | Prefix |
| --- | --- | --- |
| Bug | `Critical`, `Blocker`, `P1`, `Highest` | `hotfix/` |
| Bug | anything else, or absent | `bugfix/` |
| Story, Task, anything else | — | `feature/` |

Resolve it even when the repo's convention turns out to have no prefix: it is the fallback
in Step 3.

## Step 2 — Adopt the repository's convention

```bash
grep -rin "branch nam" AGENTS.md CONTRIBUTING.md CLAUDE.md README.md 2>/dev/null
git branch -a --sort=-committerdate | head -20
```

A stated convention wins and is named by file; many repos put the ticket key first with no
type prefix (`PROJ-1234-short-description`). Where the docs are silent, the live branches
decide; where both are silent, Step 3. A branch name is awkward to correct once a PR is
open against it, so a guess here is paid for later, usually by someone else.

## Step 3 — Build the name

`<type>/<TICKET-KEY>-<slug>`, or `<type>/<slug>` without a ticket. The key is uppercase,
exactly as Jira spells it. The slug is lowercase, hyphen-separated, 3–5 meaningful words
from the title, dropping filler ("the", "a", "issue with"), punctuation, and anything over
about 50 characters. The key and slug rules hold under a repo's own convention too; only
the prefix is in question.

`PROJ-1234 "Cart total is wrong when VAT rounding applies"` → `bugfix/PROJ-1234-cart-vat-rounding`

## Step 4 — Branch from a clean base

```bash
git fetch origin && git checkout <base> && git pull --ff-only && git checkout -b <branch-name>
```

`<base>` comes from `git symbolic-ref refs/remotes/origin/HEAD`, then `main`, then `master`.

> 🛑 **GATE — a dirty working tree.** `git status --short` is on screen.
> Ask through `AskUserQuestion`: "Uncommitted changes: stash, commit, or stop?" — options
> **stash**, **commit**, **stop**.
> Branching over work in progress silently drags it onto the new branch.

A failed `pull --ff-only` means the local base diverged: report it rather than merging or
resetting. A branch that already exists is checked out, with `branch.existed = true`; never
append `-2` to make a fresh one.
