# 0003 — A skill's name is `[<system>-]<verb>-<object>`

**Status:** accepted · 2026-09-01

## Context

Names were chosen one at a time, each sensible alone, and the set had drifted:

- **The binding was invisible.** `commit-work` and `create-branch` run git; `open-pr` and
  `resolve-pr-comments` need a forge and a token. Nothing in those names said so, so nothing
  told a reader what would fail if they lacked it.
- **No family was reachable.** Typing `/` gave one flat alphabetical list. There was no way to
  ask "what can this do with git?"
- **Verbs were ad-hoc synonyms.** `resolve-pr-comments` used *resolve*, which collides with
  GitHub's own **Resolve conversation** button — a far narrower action than what the skill
  does. The skill's own thesis reached for a better word than its title did: *"Every comment
  either earns a change or earns a reason."*
- **An abbreviation for its own sake.** `find-repo` saved three characters.

## Decision

**`[<system>-]<verb>-<object>`.**

**The prefix names a binding — the system, forge or vendor the skill cannot run without. No
binding, no prefix.** This is a fact about the skill rather than a topic label, which is what
makes it checkable and what makes a prefix worth typing.

**The verb comes from a fixed lexicon where one verb means exactly one thing.** The full table
is in [`../authoring.md`](../authoring.md) → Naming.

The renames:

| Before | After | Why |
| --- | --- | --- |
| `jira` | `atlassian-jira` | Vendor: both products share one Data Center PAT model |
| `confluence` | `atlassian-confluence` | Same |
| `commit-work` | `git-commit` | git-bound; and it is the real command's name |
| `create-branch` | `git-create-branch` | git-bound |
| `open-pr` | `git-pr-push-and-open` | Forge-bound, and the old name hid the **push** |
| `resolve-pr-comments` | `git-pr-address-review` | Forge-bound; *resolve* collided with GitHub's button |
| `find-repo` | `find-repository` | No abbreviation; no prefix — it searches directories |

Twelve skills were left alone: `plan-change`, `clarify-goal`, `write-tests`, `critique-plan`,
`record-learnings`, `explain`, `implement-ticket`, both project skills and all three `meta/`. A
rule that leaves two thirds of the set untouched is describing the naming instinct that was
already there, not replacing it.

## Consequences

- **`git-pr-` is a two-level namespace, not a claim about git.** Git has no pull requests; a
  PR is a forge concept. `git-` is the version-control family and `pr-` the forge sub-family
  within it, so `/git-` reaches all four version-control skills and `/git-pr-` narrows to the
  review loop. The alternative — a bare `pr-` — split the family in the picker for a
  correctness point the docs can make in one sentence.
- **`git-pr-push-and-open` says "push" out loud.** That is the skill's one irreversible act
  and the thing its approval gate exists to guard. A name that hid it was working against the
  gate.
- **A prefix must exclude something.** `code-` was considered and rejected: every skill in
  `engineering/` is about code, so `code-plan-change` sorts nothing — the same failure as a
  bucket everything qualifies for.
- **`publish_page.py` gains two more suffix entries.** Its resolver tuple is now six deep,
  covering every folder layout the confluence skill has lived under. Each rename adds a row
  that can never be removed while an older plugin cache might still hold it.
- **Muscle memory breaks.** Seven slash commands changed. This is the cheapest it will ever
  be — the set is nineteen skills and one user.

## Alternatives considered

**Prefix by topic** (`code-plan-change`, `code-write-tests`). Rejected above: a topic true of
the whole bucket excludes nothing.

**One verb across skills that "feel similar"** — making `write-tests` and the review skill
share a verb. Rejected: they are not the same action. Writing tests produces artifacts;
addressing a review is a triage loop with two verdicts. The fix for inconsistent verbs is a
controlled lexicon, not fewer distinct verbs.

**`microsoft-jira`.** Rejected on fact: Jira and Confluence are built by Atlassian, an
independent company. The rule — prefix with the vendor that builds it — was right; only the
vendor was misremembered.
