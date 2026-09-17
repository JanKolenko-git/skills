---
name: document
description: Write the prose about a change from its real diff and history, a PR description, a changelog or changeset entry, release notes, a postmortem or a ticket summary; every sentence traces to the record.
disable-model-invocation: true
argument-hint: <pr | changelog | release-note | postmortem | summary> [range or version]
---

# Document

Write for the reader who has to act on it, from the record rather than from memory of what
was meant to happen. A commit, a hunk or a fact the user gave is the only source a sentence
may have.

## Inputs

- `type` — **required.** `pr` | `changelog` | `release-note` | `postmortem` | `summary`.
- `range` — optional. Defaults to `<base>...HEAD` for `pr`, `changelog` and `summary`, and
  to the last two tags for `release-note`.
- `why` — the ticket, spec or plan text behind the change, passed in by the caller. Nothing
  is fetched.
- `facts` — `postmortem` only: what broke, when and for whom, how it was detected, the cause
  and the fix, from the user or a `jankolenko-skills:debug` report.
- `audience` — optional. Defaults per type: reviewers, developers, users, the team, the
  ticket's readers.

## Output

| Field | Contents |
| --- | --- |
| `document.text` | The document, ready to paste |
| `document.path` | The file written, or `chat` |
| `document.gaps` | What the record could not support, left out rather than invented |

## Step 1 — Gather the record

```bash
git log --oneline <range> && git diff --stat <range> && git diff <range>
```

Read the diff, not only the log: a commit message describes an intention, the hunk shows
what landed. For a release note, list the tags first and ask for the version and range when
there are none. Done when: every change you will name has a hunk or a commit behind it.

## Step 2 — Write to the type's shape

| Type | Shape | Goes to |
| --- | --- | --- |
| `pr` | Title under 72 characters, imperative; what; why, with the ticket or spec linked; changes grouped by intent; how to verify; risk and rollout | chat |
| `changelog` | The repository's own convention: its `CHANGELOG.md` style, or a changeset file where the repository uses them | that file |
| `release-note` | Per version, by what a user can now do, what is fixed and what they must change; internals left out | `docs/releases/<version>.md`, or the repository's own place |
| `postmortem` | Summary, impact, timeline with timezone, cause, fix, what prevents a repeat; blameless | `docs/postmortems/<date>-<slug>.md` |
| `summary` | Three to five sentences a ticket's reader can act on: what changed, where to see it, what is left | chat |

Group changes by intent, not by file or commit. Derive verification steps from the tests
and the behaviour in the diff; a step you could not derive is a row in `document.gaps`.
Match the file's existing format when the file exists. Done when: each sentence points to
a commit, a hunk or a given fact, and no sentence describes what was intended but not done.

## Step 3 — Deliver

Write the file for `changelog`, `release-note` and `postmortem`; show `pr` and `summary` in
chat in full. Opening the PR and commenting on the ticket belong to the skills that own
those writes. Done when: `document.text` is on screen and `document.path` is set.

## Notes

- Prose only: no code, tests or spec changes.
- `jankolenko-skills:git-pr-push-and-open` writes its own short PR body at push time; a
  longer description a reviewer asked for is written here and passed to it as `context`.
