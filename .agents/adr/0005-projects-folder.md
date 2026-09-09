# 0005 — Project material lives in an untracked `projects/` folder inside this repo

**Status:** accepted · 2026-09-09 · supersedes the two-repository half of
[`0004-two-repos.md`](./0004-two-repos.md); its two-plugin half stands

## Context

ADR 0004 split the skill layer into two repositories on the `projects/` membership test. A
week later the second repository was renamed on disk and nothing followed: the resolver
script, this repo's `CLAUDE.md` and `.agents/authoring.md` all named the old path, the
projects plugin failed to load, and `improve-skill` reported both project skills as someone
else's. Two clones that must agree on a path is one clone too many.

The same week showed a problem the split had not solved: the general repo was still full of
project references. `ENGINEERING.md` required every Rules entry to "name the run", so twelve
of twenty rules cited a private repository, a ticket, a PR number or a commit; the signals
ledger, three eval graders and three SKILL.md lines named one team's stack. The repo claimed
to be bound to no employer and read as one team's tooling anyway. And no rule anywhere said
whether a *rule* — as opposed to a skill — could be project-specific, or where a rule that
held for a handful of repositories should go: every routing table collapsed "not universal"
into "one repository's `CLAUDE.md`".

## Decision

**One working tree. Project material lives in `projects/`, gitignored except for the README
that documents its shape, and is organised by repository.**

```
projects/<repository>/ENGINEERING.md            rules for that repository, and the evidence it bought
projects/<repository>/skills/<skill>/SKILL.md   skills bound to that repository
projects/.claude-plugin/                        the jankolenko-projects manifest, untracked
```

Three consequences, each a decision of its own:

**The general rulebook names shapes, never coordinates.** A Rules entry in `ENGINEERING.md`
still needs one observed failure, but its `_Source:` line describes the kind of change, the
check that missed it and the tell — never a repository, ticket, PR, commit, person or private
package. The coordinates move to `projects/<repository>/ENGINEERING.md` under *Evidence
behind general rules*, so nothing is lost and the tracked file holds only what would hold in
a repository nobody here has seen. `scripts/check-portable.py` fails the tree on the three
leak shapes that can be caught mechanically.

**Rule scope is decided once, by `record-engineering-rule`, on a three-rung ladder.** Would
hold in a repository you have never seen → `ENGINEERING.md`. Holds only in repositories you
can list → `projects/<repository>/ENGINEERING.md`, one file per repository it applies to. A
fact about how one repository builds or runs that teammates should see → that repository's
own `CLAUDE.md`, via `record-learnings`. The session-start hook reads the general file
everywhere and injects the project file when the session's repository — matched by remote
name, then folder name — has one.

**Two plugins still ship, from one tree.** The general plugin is this repository; the project
plugin is rooted at `projects/`, registered as its own Directory marketplace.
`scripts/which-plugin.sh` resolves both and reports `tracked=0` for the project half, so
`improve-skill` knows there is nothing to commit there — a project edit is a manifest bump and
a `plugin update`, and a project *rules* file is not even that: the hook reads it directly.

## Rejected alternatives

**Two sibling repositories** (ADR 0004). Paths drift on rename, two clones must agree, and
the split did nothing about the project references inside the general repo.

**A nested git repository at `projects/`.** Keeps history and a remote, but reintroduces the
second clone the move was meant to remove, and the plugin cache copies the whole tree on every
update, so the general plugin's cache would carry the project repository's `.git`. The old
repository stays on GitHub as a frozen archive instead.

**A git submodule.** Tracks the project repository's URL and commit in the public tree — a
project reference in the file that exists to avoid them.

**One marketplace listing `./` and `./projects`.** A `./projects` source validates now that it
is inside the root, but the public marketplace must validate on machines where `projects/`
does not exist, so the project plugin keeps its own marketplace.

**One `ENGINEERING.md` with a section per project.** Puts the coordinates back into the
tracked file, which is the thing being removed.

**Project rules only in each repository's `CLAUDE.md`.** Team-visible, and the right place for
facts a team must share — but a personal convention for a codebase, and the evidence behind
the general rulebook, are not things to publish into a shared repository. The ladder keeps
both routes and says which is which.

**Loading project skills as personal skills from `~/.claude/skills/`.** Drops the plugin, the
bump loop and the manifest — and with them the `plugin:name` reference convention every skill
follows and the hard-dependency declaration. Left open as a later simplification.

## Consequences

- `projects/` is not a bucket. `skills/` keeps its three domain buckets and the one-level rule
  of ADR 0001; what encodes conventions only one team recognises leaves `skills/` altogether.
- `CLAUDE.md`, `record-engineering-rule`, `find-session-improvements` and the hook's three
  clauses carry the same ladder, and `record-engineering-rule` owns both the general file and
  the project files.
- Nothing under `projects/` is under version control. It is backed up with the home
  directory, and the manifest is recreated from `projects/README.md` if lost.
- The general plugin's cache will contain `projects/` — the cache copies gitignored files —
  but skills register from the manifest, so nothing loads twice.
- `scripts/check-portable.py` runs beside `scripts/list-skills.sh` before every commit. It
  cannot catch a programme's name; only a reader can.
