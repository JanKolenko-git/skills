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
Runs need a logged-in CLI; each prompt costs one model turn, because the process is killed at
the first tool call or the first finished message.

Compare before and after on the same model and the same number of runs. Triggering is
model-specific, and the number that matters is the delta, not the absolute rate.

## Baseline

Not yet measured — the CLI was logged out when the sets were written. The first run against
the current descriptions goes here, one line per skill: should-trigger passed/total,
should-not-trigger passed/total, model, runs.
