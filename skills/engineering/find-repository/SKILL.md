---
name: find-repository
description: Locate the local git repository that a piece of work belongs to, from a ticket key, a project or package name, or a few keywords — searching the current directory, $REPO_ROOT, and the usual development folders, then cross-checking package.json and git remotes. Use when the user or another skill (e.g. jankolenko-skills:implement-ticket) needs to know which repo to work in and has not been told, or asks "which repo is this ticket for?".
---

# Find Repository

Work out which local git repository a task belongs to, and stop rather than guess when the
answer is not clear.

Picking the wrong repo is expensive: every later step — branch, edits, tests, PR — lands
somewhere nobody asked for. So this skill is biased toward refusing.

## Inputs

- `hints` — **required unless `ticket_key` is given.** Anything to match on: a project name,
  a package name, a service, keywords from a task.
- `ticket_key` — optional. If given and **`jankolenko-skills:atlassian-jira` is installed**, fetch the ticket and
  derive hints from its summary, components, labels and description. If it is not installed,
  say so and ask the user for a name instead.
- `search_root` — optional. Overrides the resolution order below.

## Output

| Field | Contents |
| --- | --- |
| `repo.path` | Absolute path to the repository root |
| `repo.name` | Directory name, and `package.json` `name` if it differs |
| `repo.default_branch` | Resolved default branch |
| `repo.evidence` | Why this repo matched — the deciding signal, one line |

## Step 1 — Resolve where to look

In order, stopping at the first that yields candidates:

1. **Current directory** — if it is inside a git repo and it matches the hints, prefer it.
   Someone working in a repo and naming a ticket almost always means *this* repo.
2. **`$REPO_ROOT`** — if set, search it recursively.
3. **Common roots** — `~/Developer`, `~/code`, `~/src`, `~/projects`, `~/repos`. Search the
   ones that exist.
4. **Ask.** If none exist, tell the user to set `REPO_ROOT` and stop.

```bash
find "$ROOT" -maxdepth 3 -type d -name .git -not -path "*/node_modules/*" 2>/dev/null
```

Depth 3 covers the usual `~/Developer/<org>/<repo>` nesting without walking the world.

## Step 2 — Match

Rank candidates on:

- **Directory name** against the hints. Folder names often carry a prefix the ticket never
  mentions (`ai-`, `acme-`, `web-`) — match on the part **after** the prefix too.
- **`package.json` `name`** — cross-check it; it is often the real project name.
- **`git remote -v`** — the remote slug is frequently more accurate than the local folder.
- **Recent activity** (`git log -1 --format=%cr`) — only as a tie-breaker, never as evidence.

Ticket **components and labels** are coarse platform tags (`android`, `GW`, `frontend`), not
per-repo identifiers. Use them to narrow the candidate set, never to pick the winner.

**Where the work *ought* to live is not a signal.** "Totals are computed server-side", "that
is a UI concern" — those are claims about how systems are usually built, not evidence about
the repos in front of you, and one is available in every ambiguous case. This is how a run
reaches a single answer while holding none of the signals above.

## Step 3 — Decide

> 🛑 **GATE:** If exactly one repo matches on a substantive signal (name, package name, or
> remote), take it and report the evidence.
>
> If two or more match, or the only signal is a coarse label, **STOP.** List the top
> candidates with the reason each matched and ask which. Do not pick the most recently
> modified one and carry on.
>
> Reaching one repo by reasoning about the task rather than by a signal above is not a
> match — it is the two-candidate case with the tie broken off-book, and it stops here too.
> Naming the uncertainty and then answering anyway is the tell, not the excuse.

On success, report `repo.path` and `cd` there before any further work. Confirm the default
branch:

```bash
git -C <path> symbolic-ref --quiet refs/remotes/origin/HEAD || echo "no origin/HEAD"
```

Fall back to `main`, then `master`, if that is unset.

## Notes

- Never create a repository. If nothing matches, the answer is "I could not find it", not a
  fresh `git init`.
- If the matched repo has uncommitted changes, say so — the caller may be about to branch
  on top of someone else's work in progress.
