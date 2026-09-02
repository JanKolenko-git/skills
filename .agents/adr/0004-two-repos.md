# 0004 — Portable skills and programme skills live in separate repos

**Status:** accepted · 2026-09-02 · refines the `projects/` bucket introduced in
[`0002-domain-buckets.md`](./0002-domain-buckets.md)

## Context

One repo shipped one plugin holding all 21 skills. Nineteen were portable — the Atlassian
integrations authenticate against whatever instance `$JIRA_URL` names, and the atoms know
nothing about any employer. Two were `projects/` skills encoding adidas ML11.2 conventions:
a specific Confluence page shape, a specific gateway repo, a specific programme's vocabulary.

Shipping them together forced one decision on both halves. The portable skills are worth
publishing and reusing; the programme skills are worth neither, and their presence makes the
repo read as one team's tooling rather than as a general skill layer. A reader landing on
`ML11-2-ticket-to-confluence` cannot tell which of the other twenty are equally specific
without opening each one.

The `projects/` bucket already drew this line — [ADR 0002](./0002-domain-buckets.md) defines
its membership test as *"encodes conventions only one team recognises"*. What it did not do
was let the two halves ship, version or install independently.

## Decision

**Two repos, two plugins, split on exactly the existing `projects/` membership test.**

| Repo | Plugin | Marketplace | Buckets |
| --- | --- | --- | --- |
| `JanKolenko-git/skills` | `jankolenko-skills` | `jankolenko` | `engineering/`, `productivity/`, `meta/` |
| `JanKolenko-git/JanKolenko-Skills` | `jankolenko-projects` | `jankolenko-projects` | `projects/` |

Three consequences follow, and each was a decision of its own:

**Shared infrastructure is single-copy and lives in `jankolenko-skills`.**
`.agents/authoring.md`, the ADRs, `ENGINEERING.md`, `observations/SIGNALS.md`, the
session-start hook and `scripts/` are not duplicated. The projects repo's `CLAUDE.md` points
at them. Two rulebooks that disagree are worse than one that is occasionally wrong, and a
duplicated convention file drifts silently because nothing compares the copies.

**`meta/` goes with the portable half and stops assuming one repo.** `improve-skill` must be
able to fix a skill in either plugin, so "the source repo" is no longer a constant it can
hardcode. `scripts/which-plugin.sh` resolves repo, manifest, plugin and update command from a
skill's name, and the meta skills call it instead of guessing. The alternative — a copy of
`meta/` in each repo that only edits itself — was rejected: every meta fix would be made
twice, and the two copies would diverge on exactly the conventions they exist to enforce.

**Cross-repo references are qualified and declared.** Every reference between skills is
written `plugin:name`, which is also the string the `Skill` tool takes. The two projects
skills additionally declare `jankolenko-skills` as a **hard** dependency rather than an
optional one, because without the Atlassian integrations there is no ticket to read and no
page to write — the standing rule *optional dependencies degrade, never fail* does not apply
to a dependency whose absence removes the skill's input.

## Rejected alternatives

**One marketplace listing both plugins.** The obvious shape, and it does not work.
`claude plugin validate` rejects a plugin source containing `..` — *"Plugin source paths are
resolved relative to the marketplace root"* — and rejects absolute paths as invalid input.
Both were tested. The one form that validates alongside `"./"` is a `github` source, which
resolves the second plugin from the remote rather than the working tree: shipping a
projects-skill change to yourself would then need a push, not just a commit. That cost falls
on the half of the skill layer most likely to need a quick fix mid-task, so two Directory
marketplaces won. The price is one extra `claude plugin marketplace add` per machine, paid
once.

**Keeping `jankolenko-skills` as the projects plugin's name.** It would have avoided one
uninstall/reinstall. Rejected because the name would then sit on two skills while nineteen
moved out from under it, and every existing reference to `jankolenko-skills:git-commit` would
point at a plugin that no longer contains it.

**Splitting by public/private instead of by portability.** Both repos are public, so this was
never the real axis — the ML11.2 skills contain no secrets, only conventions nobody outside
the programme can use. Sorting by *"could someone else run this?"* keeps the test identical
to the one `projects/` already applies, which means no skill needs a second judgement call to
be placed.

## Consequences

- A skill moving between buckets may now also move between repos. `projects/` is the only
  bucket where that happens, and it is the same membership test either way.
- `find-skill-gaps` places a new skill by bucket, so it must confirm with
  `scripts/which-plugin.sh` which repo it landed in before bumping a manifest.
- `find-session-improvements` bumps **once per repo touched**, not once per retrospective.
- `publish_page.py` in the projects repo imports `_client.py` from the confluence skill. That
  import previously walked up the shared tree; with no shared ancestor it now searches
  `$JANKOLENKO_SKILLS_REPO` and the versioned plugin cache, and fails with the paths it tried
  rather than a stack trace.
