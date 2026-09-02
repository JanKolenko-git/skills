---
name: git-create-branch
description: Create a git branch named the way the repository names branches — following its own stated convention where it has one, otherwise feature/, bugfix/ or hotfix/ plus a ticket key and a short slug — branching cleanly from the default branch. Use when the user or another skill (e.g. jankolenko-skills:implement-ticket) is about to start work and needs a correctly named branch, or asks to "create a branch" or "start work on" a ticket.
---

# Git Create Branch

Create a well-named branch off the default branch, so the name says what the work is and
which ticket it answers.

## Inputs

- `type` — `feature` | `bugfix` | `hotfix`. **Optional if `ticket_key` is given** — see the
  mapping below.
- `slug` — 3–5 words describing the work, kebab-cased. Derived from the title if omitted.
- `ticket_key` — optional. If given and **`jankolenko-skills:atlassian-jira` is installed**, fetch the ticket to
  resolve `type` and `slug`. A caller that already holds the ticket data should pass
  `type`, `slug` and `ticket_key` directly rather than making this refetch.
- `base` — optional. Defaults to the repository's default branch.

## Output

| Field | Contents |
| --- | --- |
| `branch.name` | The branch created, e.g. `bugfix/PROJ-1234-cart-vat-rounding` |
| `branch.base` | What it was branched from |
| `branch.existed` | `true` if the branch already existed and was checked out instead |

## Step 1 — Resolve the type

From the ticket, when `type` was not passed:

| Issue type | Priority | Branch prefix |
| --- | --- | --- |
| Bug | Critical or Blocker | `hotfix/` |
| Bug | anything else | `bugfix/` |
| Story, Task, anything else | — | `feature/` |

Priority names vary by project. Treat `Critical`, `Blocker`, `P1` and `Highest` as the
hotfix tier; if the priority is absent or unrecognised, use `bugfix/` rather than assuming
urgency.

The type is still worth resolving even where the repo's convention turns out to have no
prefix — it is the fallback in Step 3, and it costs nothing to have ready.

## Step 2 — Adopt the repository's convention

Check how this repo names branches **before** composing a name. A branch name is awkward to
correct once it is pushed and a PR is open against it, so a guess here is paid for later and
usually by someone else.

```bash
grep -rin "branch nam" AGENTS.md CONTRIBUTING.md CLAUDE.md README.md 2>/dev/null
git branch -a --sort=-committerdate | head -20   # what the repo's branches actually look like
```

If a stated convention exists, **follow it and say which file it came from** — a repo's rule
always wins over the default below. Many repos put the ticket key first with no type prefix
at all (`PROJ-1234-short-description`), which the Step 3 format would violate.

Where the docs are silent, let the live branches decide; where both are silent, use Step 3.

## Step 3 — Build the name

When the repository states no convention of its own:

```
<type>/<TICKET-KEY>-<slug>
```

- Ticket key **uppercase**, exactly as Jira spells it.
- Slug: lowercase, hyphen-separated, 3–5 meaningful words from the title. Drop filler
  ("the", "a", "issue with"), punctuation, and anything over ~50 characters.
- Without a ticket key, `<type>/<slug>` is fine.

`PROJ-1234 "Cart total is wrong when VAT rounding applies"` → `bugfix/PROJ-1234-cart-vat-rounding`

The key and slug rules hold under a repo's own convention too — only the prefix is in
question.

## Step 4 — Branch from a clean base

```bash
git fetch origin
git checkout <base>
git pull --ff-only
git checkout -b <branch-name>
```

Resolve `<base>` from `git symbolic-ref refs/remotes/origin/HEAD`, falling back to `main`
then `master`.

> 🛑 **GATE:** If the working tree has uncommitted changes, **STOP** and show
> `git status --short`. Branching over someone's work in progress silently drags it onto the
> new branch. Ask whether to stash, commit, or abort.

If `pull --ff-only` fails, the local base has diverged — report it rather than merging or
resetting. That is a state the user should see.

If the branch already exists, check it out instead of failing, and set `branch.existed`.
Do not append `-2` to make a fresh one.
