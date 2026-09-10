# Trigger evals

One JSON set per model-invoked skill: the prompts its description should fire on, and the
near-misses it should stay quiet on. `scripts/trigger-eval.py` runs each prompt through
`claude -p` against the real skill listing — every installed plugin, plus this working tree
loaded with `--plugin-dir` so the description under test is the one on disk — and records
whether the first tool call was `Skill` naming that skill.

The refusal cases in `evals/<case>/` test what a skill does once it runs. These test whether
it runs at all, which is the description's job and nothing else's.

## Format

```json
[
  {"query": "whats in PROJ-1155 ticket?", "should_trigger": true},
  {"query": "implement PROJ-412 end to end", "should_trigger": false, "instead": "implement-ticket"}
]
```

`instead` names the skill a near-miss belongs to, so a failure reports which skill won. It is
optional and ignored by `anthropic-skills:skill-creator`'s `run_eval.py`, which reads the same
format.

The prompts are drawn from real session openers, with every ticket key, host, repository and
person replaced by a placeholder (`PROJ-1234`, `jira.example.com`, `storefront-web`).
Keep them that way: `scripts/check-portable.py` scans these files too. Keep the typos and the
casual phrasing; a set of tidy prompts tests a user who does not exist.

Negatives are the valuable half. A negative that shares no words with the skill tests
nothing; the ones worth having name the competing skill (`explain` vs `plan-change`,
`write-tests` vs `mattpocock-skills:tdd`, `git-commit` vs `git-pr-push-and-open`) or a plain
request that needs no skill at all.

## Running

```bash
scripts/trigger-eval.py --skill plan-change                 # one run per prompt
scripts/trigger-eval.py --skill plan-change --runs 3        # the gate for a description change
scripts/trigger-eval.py --skill plan-change --model claude-sonnet-5 --json out.json
```

A prompt passes when its trigger rate lands on the right side of 0.5. Exit 1 on any failure.
Runs need a logged-in CLI. Each prompt costs one to three short turns: the process is killed
as soon as the skill fires, three other tool calls have been seen, or the message ends.

Compare before and after on the same model and the same number of runs. Triggering is
model-specific, and the number that matters is the delta, not the absolute rate.

## Baseline

Measured 2026-09-10 against the descriptions as they stood before Phase 1, on
`claude-sonnet-5`, one run per prompt, the first three tool calls watched, a scratch git
repository as the working directory. Raw results: `evals/results/triggers-2026-09-10/`
(untracked).

| Skill | Should trigger | Should not trigger |
| --- | --- | --- |
| `atlassian-confluence` | 6/8 | 8/8 |
| `atlassian-jira` | 8/10 | 5/7 |
| `critique-plan` | 5/6 | 8/8 |
| `draft-reply` | 4/8 | 7/7 |
| `explain` | 7/10 | 7/7 |
| `find-repository` | 5/7 | 8/8 |
| `git-commit` | 2/8 | 8/8 |
| `git-create-branch` | 6/6 | 8/8 |
| `git-pr-address-review` | 4/8 | 7/7 |
| `git-pr-push-and-open` | 2/8 | 7/7 |
| `implement-ticket` | 5/7 | 8/8 |
| `improve-skill` | 3/7 | 7/7 |
| `plan-change` | 5/9 | 8/8 |
| `prepare-local-environment` | 5/9 | 7/7 |
| `record-engineering-rule` | 6/7 | 7/7 |
| `record-learnings` | 2/6 | 8/8 |
| `write-tests` | 3/7 | 8/8 |
| **all 17** | **78/131 (60%)** | **126/128 (98%)** |

Under-triggering is the whole problem: near-misses stay quiet (two leaks, both into
`atlassian-jira` from prompts that begin by reading a ticket), while two in five prompts that
should fire a skill do not. The dominant miss is the model doing the thing itself — `git
commit`, `git push`, `npm run dev`, a grep for the repo — through Bash, which is exactly
where the gates those skills carry are skipped. The five weakest: `git-commit` 2/8,
`git-pr-push-and-open` 2/8, `record-learnings` 2/6, `improve-skill` 3/7, `write-tests` 3/7.
Two `implement-ticket` prompts fired `atlassian-jira` instead; a prompt typed as
`/implement-ticket PROJ-4412` counts among them, because print mode does not resolve an
unqualified slash command and the model read it as text.

One run per prompt is noise at the level of a single prompt; the per-skill totals and the
direction are what to compare against after a rewrite, on the same model and settings.

## After Phase 1

Same model, settings and sets as the baseline (`claude-sonnet-5`, one run per prompt),
against the rewritten descriptions. Each cell is should-fire · near-miss quiet. The last
column is a three-run check on the skills whose one-run number moved. Raw results:
`evals/results/triggers-2026-09-10-phase1*/` (untracked).

| Skill | Baseline | After Phase 1 | Three runs |
| --- | --- | --- | --- |
| `atlassian-confluence` | 6/8 · 8/8 | 6/8 · 8/8 |  |
| `atlassian-jira` | 8/10 · 5/7 | 9/10 · 5/7 |  |
| `critique-plan` | 5/6 · 8/8 | 6/6 · 8/8 |  |
| `draft-reply` | 4/8 · 7/7 | 6/8 · 7/7 |  |
| `explain` | 7/10 · 7/7 | 6/10 · 7/7 | 8/10 · 7/7 |
| `find-repository` | 5/7 · 8/8 | 5/7 · 8/8 |  |
| `git-commit` | 2/8 · 8/8 | 3/8 · 8/8 | 2/8 · 8/8 |
| `git-create-branch` | 6/6 · 8/8 | 6/6 · 8/8 |  |
| `git-pr-address-review` | 4/8 · 7/7 | 6/8 · 7/7 |  |
| `git-pr-push-and-open` | 2/8 · 7/7 | 2/8 · 7/7 | 2/8 · 7/7 |
| `implement-ticket` | 5/7 · 8/8 | 5/7 · 8/8 |  |
| `improve-skill` | 3/7 · 7/7 | 2/7 · 7/7 | 5/7 · 7/7 |
| `plan-change` | 5/9 · 8/8 | 7/9 · 8/8 |  |
| `prepare-local-environment` | 5/9 · 7/7 | 7/9 · 6/7 | 7/9 · 6/7 |
| `record-engineering-rule` | 6/7 · 7/7 | 5/7 · 7/7 | 6/7 · 7/7 |
| `record-learnings` | 2/6 · 8/8 | 5/6 · 8/8 |  |
| `write-tests` | 3/7 · 8/8 | 3/7 · 8/8 |  |
| **all 17** | **78/131 (60%) · 126/128 (98%)** | **89/131 (68%) · 125/128 (98%)** | |

Should-fire rose from 60% to 68% with near-misses unchanged, and every skill whose one-run
number dipped holds at or above its baseline over three runs. The `prepare-local-environment`
near-miss that now fires ("my local server 500s on every page after the branch switch") was
mislabelled: a stale install after a branch switch is the case the skill was reworded for, so
that prompt is a positive from now on.

Two things the measurement itself taught. A hook sentence routing commits, pushes and skill
edits to their skills was tried and dropped: an A/B on the default model showed no
difference (`git-commit` 8/8 in both arms, `git-pr-push-and-open` 6/8 against 7/8). And the
default model fires those two guardrail skills 8/8 and 7/8 where Sonnet 5 manages 2/8 on the
same prompts, so the low Sonnet numbers are a property of the measuring model, not of the
descriptions; Sonnet stays the measuring model because the delta is what the gate checks.
