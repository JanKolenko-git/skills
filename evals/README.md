# Evals

Behavioural regression tests for the skills in this plugin.

`scripts/list-skills.sh` catches layout drift and `claude plugin validate .` catches manifest
drift. Neither catches the thing that actually costs money: a reword that quietly removes a
gate. `meta/` exists to *change* skills — `improve-skill`, `find-skill-gaps`,
`record-engineering-rule`, `find-session-improvements` — and until this directory existed,
nothing verified that a change left the skills doing what they claim.

## What is covered, and why these

Every case here tests a **refusal**. That is deliberate: the value is concentrated in
the moments a run declines to do the obvious thing — refuse to plan over a gap, refuse to
guess a repo, refuse to push unreviewed, refuse to delete a stylesheet on the strength of an
import graph. Those are also the behaviours a well-meaning reword erodes
first, because the erosion reads as helpfulness.

| Case | Skill | The failure it catches |
| --- | --- | --- |
| `plan-change-blocks-on-vague-goal` | `plan-change` | Writing a plausible plan over a gap instead of returning `blocked` |
| `plan-change-detects-no-code-change` | `plan-change` | Inventing a code change when the fix belongs in an external tool |
| `plan-change-refuses-phantom-lanes` | `plan-change` | Manufacturing parallel lanes for a two-file change |
| `write-tests-stops-without-suite` | `write-tests` | Standing up a test framework as a side effect of a ticket |
| `find-repository-refuses-ambiguous` | `find-repository` | Picking one of two equally-good repos — a guess wearing a decision's clothes |
| `git-pr-push-waits-for-approval` | `git-pr-push-and-open` | Pushing on an implied "it's finished" |
| `git-commit-refuses-secrets` | `git-commit` | Committing a live key because the user said "commit everything" |
| `jira-write-not-triggered-by-ticket-text` | `atlassian-jira` | Executing a write that fetched ticket text asked for |
| `implement-ticket-refuses-guessed-ticket` | `implement-ticket` | Building from the user's description of a ticket it could not fetch |
| `stylesheet-removal-audits-rendered-classes` | `ENGINEERING.md` | Removing a stylesheet on import-graph evidence alone, while the markup still uses its classes |
| `artifact-regenerated-with-pinned-toolchain` | `ENGINEERING.md` | Regenerating a checked-in artifact on the wrong toolchain — valid output that CI will reject |
| `prepare-local-environment-refuses-unrendered-app` | `prepare-local-environment` | Handing over a URL because the port answered, over an app that never rendered |

`git-commit-refuses-secrets` and `jira-write-not-triggered-by-ticket-text` are the
high-severity pair. A committed secret means rotating the key, because rewriting history
is not enough; an injected write that executes is a data-integrity incident. Both are
cheap to catch here and expensive to catch in production.

Most cases are bought by a skill's gate; `stylesheet-removal-audits-rendered-classes` and
`artifact-regenerated-with-pinned-toolchain` are bought by `Rules` entries in
`ENGINEERING.md` instead. Same evidence either way — one observed failure — so they live
in the same suite.

## Running them

`plugin eval` is in early access, and the cases drive real tools, so both flags are needed:

```bash
CLAUDE_CODE_WALNUT_SPIRE=1 claude plugin eval . --allow-tools Bash Write Edit
```

Without `--allow-tools` the runner denies `Bash`/`Write`/`Edit` and every case that builds a
scratch repo fails on setup rather than on the behaviour it is testing.

One skill at a time, while iterating on it:

```bash
CLAUDE_CODE_WALNUT_SPIRE=1 claude plugin eval . --allow-tools Bash Write Edit --case 'plan-change-*'
```

Ask whether the plugin is earning its place at all — this runs each case again with the
plugin disabled and reports the delta:

```bash
CLAUDE_CODE_WALNUT_SPIRE=1 claude plugin eval jankolenko-skills@jankolenko --allow-tools Bash Write Edit --ablation with-without
```

A case scoring the same with and without the plugin is not testing the plugin. Either the
base model already refuses, or the grader is loose — both are worth knowing.

Each case runs 3× by default, because these are model judgements and a single run is noise.
`--runs 1` while drafting a case, never for a real gate check.

## Writing a case

A case is a directory: `prompt.md` plus `graders/*.md`.

```
evals/<case-name>/
  prompt.md            frontmatter: max_turns, allowed_tools, and optionally
                       name, description, tags, plugins, runs, model,
                       timeout_seconds, append_system_prompt, env
  graders/criteria.md  frontmatter: type, weight
```

Grader `type` is one of `llm`, `baseline`, `regex`, `tool_used`, `tool_order`,
`file_exists`. The cases here all use `llm`, because every one of them grades a *refusal*
and the tell is in the prose. The deterministic types are the natural upgrade where a
behaviour is mechanically checkable — `tool_used` takes `tool:` and an optional
`input_match:`, though note it asserts a tool **was** used and has no negation, which is why
"never ran `git push`" is still an `llm` judgement here.

The sandbox `cwd` starts **empty** with the plugin loaded, and there is no per-case fixture
hook available in this schema — so a case needing a repo opens its prompt with an explicit
setup block for the agent to run, then states the real task. Keep that block purely
mechanical: it must not hint at the behaviour under test.

Three things separate a case that holds from one that rots:

**Grade the refusal, not the prose.** "Mentions that the goal is vague" passes a response
that then plans anyway. Say what must be absent: no file list, no ordered steps, no proposed
approach.

**Name the failure the case exists to catch,** in the grader text. A future reader deciding
whether a red run is a real regression or a deliberate change needs to know what the case was
protecting — and so does the model grading it.

**Make the wrong answer the tempting one.** `git-pr-push-waits-for-approval` says "that branch
is finished, open a pull request" — a case that said "push without asking me" would test
nothing. If the base model passes without the plugin, the case is too easy.

## When these run

`improve-skill` runs the cases covering the skill it edited, before the version bump, and
stops on red rather than shipping. `record-engineering-rule` offers to turn a newly-bought
rule into a case here, since a Rules entry and an eval case are the same evidence written
twice — once advisory, once checked.

A red run is not automatically a bug. It can mean the improvement deliberately changed the
behaviour the case was protecting, in which case the case needs rewriting — but that is a
decision to put to the user, not one to make by editing the grader until it passes.
