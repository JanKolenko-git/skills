---
name: review
description: Review a diff for bugs with a panel of three models, haiku, sonnet and opus, each in its own agent on one brief, the findings merged by agreement and verified against the code. Use when the user asks for a panel review, a review by several models, or a second opinion on a diff. A single-model review is /code-review.
---

# Review

Three models read the same diff on the same brief, and a bug two of them name is rarely
noise. The `review-panel` workflow seats the panel, merges what comes back by agreement
and verifies every finding against the code. This skill scopes the diff, prices the run,
starts it and reports. It writes nothing.

## Inputs

- `diff` — optional. Defaults to the branch and working tree against `base`, untracked
  files included.
- `base` — optional. Defaults to the default branch, `origin/<default>` when there is a
  remote.
- `models` — optional. Defaults to `haiku, sonnet, opus`. The session's own model verifies,
  so it never sits on the panel.
- `focus` — optional. Files or a concern to weight: "the retry path", "hydration".

## Output

| Field | Contents |
| --- | --- |
| `review.findings` | One row per distinct finding: file and line, claim, failure scenario, the seats that raised it, verdict `confirmed` / `refuted` / `unverified` with one line of why |
| `review.panel` | Per seat: model requested, model reported, raised, confirmed, refuted; tokens from `/workflows` |
| `review.missing` | Seats whose agent returned nothing |

Bugs only: a failure the code can produce. Style, naming and test quality belong to
`/simplify`, and whether the change should exist to `jankolenko-skills:check`.

## Step 1 — Establish the diff

Write the diff of the branch and working tree against the merge-base with `base` to one
file in the scratchpad, untracked files appended, so every seat reads the same bytes.

```bash
git fetch -q origin 2>/dev/null; git diff "$(git merge-base <base> HEAD)" > review.diff; git ls-files --others --exclude-standard
```

Done when: the file exists and the touched files are listed with their line counts.

## Step 2 — State the fan-out, then run the workflow

Print one line before anything runs: `3 seats + <files> verifiers, haiku, sonnet, opus,
read-only, ≈ <estimate>`, at about 50K tokens of boot per agent plus what it reads. Then
run the workflow by name through the `Workflow` tool: `name: jankolenko-skills:review-panel`,
`args: { diffPath, repo, base, focus, models }`. It seats one `jankolenko-skills:panelist`
per model with one brief, merges findings by file and line within three, and sends each
file's findings to one verifier on the session's model. `/workflows` shows tokens per
agent while it runs.

| The run | Do |
| --- | --- |
| Returns | Step 3 |
| Returns `panel: false` | Two seats reported the same model. Report the rows as one model's review, name the seats, and say so first |
| `Workflow` tool absent or disabled | One `Agent` call per model in a single message, `subagent_type: jankolenko-skills:panelist`, `model` per call, the brief from the Find stage of `${CLAUDE_PLUGIN_ROOT}/workflows/review-panel.js`. Merge and verify in the session by the same rules, and say so once |

Done when: the run has returned, or the fallback's seats have reported and every row has
a verdict.

## Step 3 — Report

`review.findings` from the run's `findings`, confirmed first, then by how many seats raised
it. Under it `review.panel` from `seats`, one row per seat, so the cost of each stays
visible over time. Nothing confirmed: say so, with what the seats read.

| # | File:line | Claim | Failure scenario | haiku | sonnet | opus | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `src/api/client.ts:88` | `res.ok` never checked | a 500 becomes a JSON parse error two layers up | ✓ | ✓ | ✓ | confirmed |
| 2 | `src/cart/total.ts:42` | discount applied before the zero-quantity guard | qty 0, 10% off → negative total | | ✓ | ✓ | confirmed |
| 3 | `src/utils/date.ts:9` | month-end off by one | 31 Jan + 1 month | ✓ | | | refuted: `Intl` clamps, tested on line 40 |

## Notes

- Reports only. A confirmed finding goes to the builder, or to `jankolenko-skills:debug`
  when its cause is not yet known.
- `/code-review` is the one-model review, `/simplify` the quality pass,
  `jankolenko-skills:check` the intent check.
- `models` may seat two, or add `fable`. The estimate line moves with it.
- `/jankolenko-skills:review-panel` by hand skips this skill: the workflow scopes the diff
  itself and returns the raw result.
