# 0002 — Buckets sort by domain, not role

**Status:** accepted · 2026-09-01 · supersedes the "Adopt mattpocock's buckets wholesale"
alternative rejected in [`0001-one-bucket-level.md`](./0001-one-bucket-level.md)

## Context

`skills/` sorted by **role**: `integrations/`, `atoms/`, `orchestrators/`, `projects/`,
`meta/`. [ADR 0001](./0001-one-bucket-level.md) considered adopting
[mattpocock/skills](https://github.com/mattpocock/skills)' domain buckets and rejected it,
on the grounds that the role order _is_ the dataflow and that this is load-bearing for how
skills here are wired.

That rejection conflated two things: whether the role distinction is valuable (it is), and
whether it should be expressed as folders (it need not be).

Three problems with role-as-folder surfaced:

- **The buckets don't answer the question a reader asks.** Someone looking for a skill knows
  what they want to _do_, not what internal role it plays. `atoms/` and `orchestrators/` are
  a maintainer's distinction sitting in the reader's way.
- **Role is the mutable axis; domain is the stable one.** A skill's domain effectively never
  changes. Its role does — an atom that grows a second caller becomes an orchestrator. Under
  role-as-folder, saying so costs a folder move, every relative link into it, a `plugin.json`
  path change and a version bump. The axis that changes most often was the one nailed to the
  filesystem.
- **Nothing enforced it anyway.** No check ever verified that a skill in `atoms/` had explicit
  inputs, or that an `orchestrators/` skill owned no mechanics. The folder asserted a
  contract it could not hold.

## Decision

**Buckets sort by domain. Role stops being a folder and stays a property of the skill.**

| Bucket          | Test for membership                                                 |
| --------------- | ------------------------------------------------------------------- |
| `engineering/`  | The output is a diff, a branch, a PR, or a ticket updated about one |
| `productivity/` | Useful with no repo open at all                                     |
| `projects/`     | Encodes conventions only one team recognises                        |
| `meta/`         | Reads or edits this repo, never a work repo                         |

Role — **integration**, **atom**, **orchestrator** — groups the entries inside each bucket's
`README.md`, which is where the dataflow stays visible. Each role is recognisable from the
skill file itself (env vars, explicit inputs, or an explicit statement for orchestrators,
which are the one case shape does not reveal), so no decorative role label is added to the
eighteen skills that never needed one. Documented in [`../authoring.md`](../authoring.md)
under "Two axes".

The moves:

| Before                                   | After                                   |
| ---------------------------------------- | --------------------------------------- |
| `skills/integrations/{jira,confluence}/` | `skills/engineering/{jira,confluence}/` |
| `skills/atoms/*/` (10 skills)            | `skills/engineering/*/`                 |
| `skills/atoms/explain/`                  | `skills/productivity/explain/`          |
| `skills/orchestrators/implement-ticket/` | `skills/engineering/implement-ticket/`  |

`projects/` and `meta/` are unchanged: both were already domain buckets wearing a role label.

## Consequences

- **The vocabulary survives the folders.** "Atom" and "orchestrator" remain the words the
  README, `authoring.md` and `implement-ticket` are written in. `implement-ticket` still opens
  "This skill is an **orchestrator**"; it just no longer lives in a folder that repeats it.
  This is the same move mattpocock/skills makes with its user-invoked / model-invoked axis —
  a real distinction, documented in `.agents/`, not a directory.
- **Bucket READMEs now carry the role grouping**, which lets them say _why_ a group coheres
  rather than only that it does. `engineering/README.md` has three role sections.
- **`productivity/` ships with one skill** (`explain`). A bucket of one is thin, and it is
  kept deliberately: the boundary is cheaper to draw now than to retrofit at three.
- **`publish_page.py` gains `('engineering', 'confluence')`** at the head of its suffix tuple
  and keeps every older entry. That tuple is now a three-entry record of taxonomy churn,
  which is itself the argument for not moving folders casually.
- **Paths in `plugin.json` change again.** Both this and ADR 0001 ship in one 3.6.0 bump,
  since neither was released separately.

## What would reverse this

If `productivity/` never gains a second skill and `engineering/` grows past roughly twenty,
the domain split will have bought nothing while `engineering/` becomes the undifferentiated
pile that `atoms/` and `orchestrators/` at least avoided. The fix then is not to restore role
folders but to split `engineering/` on a finer domain line — review, delivery, planning.
