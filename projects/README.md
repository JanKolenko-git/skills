# projects/

Machine-local and untracked. This folder holds everything the skill layer knows about
*specific* repositories: the rules that hold in one codebase but not in one you have never
seen, and the skills bound to one team's conventions. `.gitignore` excludes all of it except
this file, so the tracked repo stays general and this folder can name tickets, PRs, commits,
people and private packages freely. Why it is shaped this way:
[`.agents/adr/0005-projects-folder.md`](../.agents/adr/0005-projects-folder.md).

## Layout

```
projects/
  README.md                               this file — the only tracked one
  .claude-plugin/plugin.json              the jankolenko-projects manifest — untracked
  .claude-plugin/marketplace.json
  <repository>/ENGINEERING.md             rules for that repository, and the evidence it bought
  <repository>/skills/<skill>/SKILL.md    skills bound to that repository
```

One folder per repository, named as the repository's **remote** names it (`storefront-web`,
not a local checkout's folder name), because that is the key the session-start hook matches
on. A folder may hold rules, skills, or both.

## `<repository>/ENGINEERING.md`

Same entry shape as the root [`ENGINEERING.md`](../ENGINEERING.md), opposite provenance
rule: here the `_Source:` line names the ticket, the PR and the commit, because here they
are the point.

```markdown
# <repository>

Rules that hold in this repository and not in one you have never seen. The root
ENGINEERING.md is the general rulebook; nothing here restates it.

## Rules

### <the rule, as a sentence>

<the yes and the no, why it matters here, the exception>

_Source: <ticket>, <PR>, <commit>._

## Evidence behind general rules

- **<heading of the root ENGINEERING.md entry>** — what happened in this repository:
  ticket, PR, commit, the numbers.
```

The session-start hook injects this file for the repository a session opens in — it reads
`git remote get-url origin`, then falls back to the toplevel folder name — so a rule written
here is read before code changes in that repository, right after the general rules. No
version bump is involved; the hook reads the folder directly.

Where a rule goes is decided once, in `jankolenko-skills:record-engineering-rule`:

| The rule… | Goes to |
| --- | --- |
| would hold in a repository you have never seen | root `ENGINEERING.md` — the *shape* of the failure, no identifiers |
| holds only in repositories you can list — one team, one stack, one repo | `projects/<repository>/ENGINEERING.md`, one file per repository it applies to |
| is a fact about how one repo builds or runs that teammates should see | that repo's own `CLAUDE.md`, via `jankolenko-skills:record-learnings` |

## `<repository>/skills/<skill>/`

Skills that encode conventions only one team recognises. They ship as the
`jankolenko-projects` plugin, rooted at this folder, and load as
`jankolenko-projects:<skill>` exactly as the general ones load as `jankolenko-skills:<skill>`.
Each follows [`.agents/authoring.md`](../.agents/authoring.md) like any other skill and
declares `jankolenko-skills` as a hard dependency when it needs the Atlassian integrations.

The manifest is untracked, so if it is ever lost it is recreated from this shape, with a
`marketplace.json` beside it naming one plugin, `jankolenko-projects`, source `./`:

```json
{
  "name": "jankolenko-projects",
  "version": "1.0.0",
  "description": "One team's workflows. Builds on the jankolenko-skills plugin one level up.",
  "license": "MIT",
  "skills": ["./<repository>/skills/<skill>"]
}
```

## Registering it (once per machine)

```bash
claude plugin marketplace add ~/Developer/skills/projects
claude plugin install jankolenko-projects@jankolenko-projects
```

After editing a project *skill*, bump `version` in the manifest and run
`claude plugin update jankolenko-projects@jankolenko-projects` — sessions load skills from
the versioned plugin cache. `scripts/which-plugin.sh <skill>` prints that command, and
`tracked=0`, for any skill that lives here; there is nothing to commit.

Override the location with `$JANKOLENKO_PROJECTS_DIR`. The default is `projects/` under
`$JANKOLENKO_SKILLS_REPO` (`~/Developer/skills`).

## Backup

Nothing here is under version control. Back the folder up the way you back up the rest of
your home directory.
