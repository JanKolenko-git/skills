---
name: find-repository
description: Find the git repository a task belongs to, from a ticket key, package name or keywords: searches $REPO_ROOT and the usual code folders, checks package.json names and remotes, refuses to guess between two matches. Use when the user asks which repo something is about or which repo owns or consumes a package, or work must start with no repo named.
---

# Find Repository

Work out which local git repository a task belongs to, and stop rather than guess. Picking
the wrong repo is expensive: every later step (branch, edits, tests, PR) lands somewhere
nobody asked for, so this skill is biased toward refusing.

## Inputs

- `hints` — **required.** Anything to match on: a project name, a package name, a service,
  keywords, a ticket's title, components and labels. A caller holding a ticket passes these
  from it. This skill fetches nothing.
- `search_root` — optional. Overrides the resolution order below.

## Output

| Field | Contents |
| --- | --- |
| `repo.path` | Absolute path to the repository root |
| `repo.name` | Directory name, and `package.json` `name` if it differs |
| `repo.default_branch` | Resolved default branch |
| `repo.evidence` | The deciding signal, one line |

## Step 1 — Resolve where to look

In order, stopping at the first that yields candidates:

1. The current directory, when it is inside a git repo that matches the hints. Someone
   working in a repo and naming a ticket almost always means this repo.
2. `$REPO_ROOT`, searched recursively.
3. The common roots: `~/Developer`, `~/code`, `~/src`, `~/projects`, `~/repos`.
4. Nothing found: ask the user to set `REPO_ROOT` and stop.

```bash
find "$ROOT" -maxdepth 3 -type d -name .git -not -path "*/node_modules/*" 2>/dev/null
```

## Step 2 — Match

| Signal | Weight |
| --- | --- |
| Directory name against the hints | Decides. Folder names often carry a prefix the ticket never mentions, so match the part after it too |
| `package.json` `name` | Decides |
| `git remote -v` slug | Decides. Often more accurate than the folder |
| Recent activity | A tie-breaker, never evidence |
| Ticket components and labels | Coarse platform tags: they narrow the set and never pick the winner |
| Where the work *ought* to live ("totals are computed server-side") | None. A claim about systems in general, not evidence about the repos in front of you, and available in every ambiguous case |

## Step 3 — Decide

Exactly one repo matching on a deciding signal is the answer. Report it with
`repo.evidence`. Make `repo.path` the session's directory with the host's change-directory
tool when it has one, else work through absolute paths and `git -C`: a shell `cd` does not
last between calls. Resolve the default branch with
`git symbolic-ref --quiet refs/remotes/origin/HEAD`, falling back to `main` then `master`.

> 🛑 **GATE — an ambiguous match.** Two or more repos match, or the only signal is a coarse
> label. One repo reached by reasoning about the task, rather than by a deciding signal, is
> ambiguous too.
> Ask through `AskUserQuestion`: "Which repository is this about?" — one option per
> candidate with the reason it matched, plus **stop**.
> Naming the uncertainty and then answering anyway is the tell, not the excuse. Standing
> rule: refuse rather than guess.

## Notes

- Never create a repository: if nothing matches, the answer is "I could not find it".
- If the matched repo has uncommitted changes, say so. The caller may be about to branch on
  top of someone's work in progress.
