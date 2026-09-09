# 0001 — One bucket level under `skills/`

**Status:** accepted · 2026-09-01

## Context

`skills/` started as five role buckets — `integrations/`, `atoms/`, `orchestrators/`,
`projects/`, `meta/` — with skills sitting directly inside them. Two buckets then grew a
second grouping level as they filled up:

```
skills/integrations/atlassian/jira/SKILL.md
skills/projects/P1.2/ticket-to-confluence/SKILL.md
```

The grouping folders (`atlassian/`, and `P1.2/` — a programme's name, placeholder here) were
doing real conceptual work — vendor and programme are genuine facts about those skills — but
they were paid for in three places:

- **Relative links.** Cross-bucket references were written as `../../../integrations/atlassian/jira/SKILL.md`.
  Depth-dependent link prefixes silently break on any move, and nothing checks them.
- **Runtime path resolution.** `publish_page.py` reuses the confluence skill's `_client.py`
  and has to locate it at runtime. It already carried a tuple of _every historical folder
  suffix_ the confluence skill has lived under, because a previous regrouping had broken the
  import once. Each new grouping level adds another entry it must never drop.
- **Name/folder disagreement.** `skills/projects/P1.2/ticket-to-confluence/` declared
  `name: P1.2-ticket-to-confluence`, which Claude Code registers as
  `P1-2-ticket-to-confluence`. Two spellings and a dot that survives in one and not the
  other, needing a four-line footnote in the SKILL.md to explain which one invokes it.

The reference point is [mattpocock/skills](https://github.com/mattpocock/skills), which puts
every skill at exactly `skills/<bucket>/<skill-name>/` and carries the grouping in a bucket
`README.md` instead.

## Decision

**Every skill lives at exactly `skills/<bucket>/<skill-name>/SKILL.md`.** One bucket level,
never two. The folder name is the skill's `name` verbatim, hyphens only, no dots.

Grouping that a bucket still wants is expressed in that bucket's `README.md` — prose, which
can say _why_ two skills belong together, rather than a folder, which can only say _that_
they do.

Concretely:

| Before                                               | After                                                |
| ---------------------------------------------------- | ---------------------------------------------------- |
| `skills/integrations/atlassian/jira/`                | `skills/integrations/jira/`                          |
| `skills/integrations/atlassian/confluence/`          | `skills/integrations/confluence/`                    |
| `skills/projects/P1.2/verify-ticket/`                | `skills/projects/P1-2-verify-ticket/`                |
| `skills/projects/P1.2/ticket-to-confluence/`         | `skills/projects/P1-2-ticket-to-confluence/`         |

The two project skills' frontmatter `name` loses its dot to match the folder. The invocable
name is unchanged — `/P1-2-ticket-to-confluence` worked before and works now — because the
dot was already being normalised away at registration.

## Consequences

- The vendor fact (_these two are Atlassian_) and the programme fact (_these two are one
  programme's_) now live in `skills/integrations/README.md` and `skills/projects/README.md`. They are no
  longer enforced by the filesystem, so a future non-Atlassian integration simply sits beside
  jira and confluence rather than forcing a decision about a new vendor folder.
- Cross-bucket relative links are uniformly `../../<bucket>/<skill>/SKILL.md`. One depth, for
  every skill, forever — which is the property that makes them checkable.
- `publish_page.py` gains `('integrations', 'confluence')` at the head of its suffix tuple and
  keeps every older entry, so a plugin cache still holding the old layout keeps working.
- Adding a skill is now four edits, and `scripts/list-skills.sh` fails until all four are
  done: the skill folder, its bucket `README.md`, the root `README.md`, and the `skills` array
  in `.claude-plugin/plugin.json`.
- The paths in `plugin.json` changed, so this ships as a minor bump (3.6.0) and users need
  `claude plugin update jankolenko-skills@jankolenko` — an unversioned edit would leave sessions loading
  the old cache.

## Alternatives considered

**Keep the grouping folders and fix the links.** Rejected: it treats the symptom. The runtime
resolver in `publish_page.py` exists _because_ the depth has changed twice; a third grouping
level would extend the same tuple again. The cost is not the current links, it is that the
depth is a variable at all.

**Adopt mattpocock's buckets wholesale** (`engineering/`, `productivity/`, `misc/`,
`personal/`, `in-progress/`, `deprecated/`). Rejected: those buckets sort by audience and
lifecycle. Ours sort by role, and the order _is_ the dataflow — integrations feed atoms, atoms
compose into orchestrators, orchestrators specialise into projects, meta watches all of it.
That is load-bearing for how skills here are written and wired. The shape was worth copying;
the semantics were not.

> **Superseded by [0002](./0002-domain-buckets.md).** This rejection conflated whether the
> role distinction is valuable with whether it should be a folder. It is valuable, and it is
> now a declared property instead — which keeps the dataflow argument above intact while the
> buckets sort by domain. The decision recorded in _this_ ADR — one bucket level, folder name
> equal to skill name — is unaffected and still stands.

> **Refined by [0005](./0005-projects-folder.md).** `projects/` is no longer a bucket under
> `skills/` at all: project skills live at `projects/<repository>/skills/<skill>/`, untracked,
> and the programme-name placeholders above describe a layout this repo no longer has. The
> one-level rule still governs everything under `skills/`.
