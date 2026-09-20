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
| `branch.path` | Where the branch is checked out: the repository, or the worktree made for it |

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

## Step 4 — Branch in place, or in a worktree

A free checkout, clean and on the default branch, branches in place:

```bash
git fetch origin && git checkout <base> && git pull --ff-only && git checkout -b <branch-name>
```

`<base>` comes from `git symbolic-ref refs/remotes/origin/HEAD`, then `main`, then `master`.
A busy checkout is dirty or on another branch. The user's word ("in a worktree", "here")
decides where the branch goes. Without it:

> 🛑 **GATE — a busy checkout.** `git status --short` and the current branch are on screen.
> Ask through `AskUserQuestion`: "Where should `<branch-name>` go?" — options **worktree**
> (recommended), **switch this checkout**, **stop**.
> worktree → the commands below. switch this checkout → stash what is uncommitted, name the
> stash in the report, then branch in place. stop → end with nothing changed.
> A busy checkout may belong to a parallel session, and branching over work in progress
> drags it onto the new branch.

```bash
git fetch origin && git worktree add -b <branch-name> ../<repo>-wt-<TICKET-KEY> origin/<base>
cp -n .env* ../<repo>-wt-<TICKET-KEY>/ 2>/dev/null   # untracked env files come along
```

The report names the command that removes the worktree:
`git worktree remove ../<repo>-wt-<TICKET-KEY>`.

A failed `pull --ff-only` means the local base diverged: report it rather than merging or
resetting. A branch that already exists is checked out, with `branch.existed = true`. Never
append `-2` to make a fresh one.
