---
name: architect
description: Settle a technical decision that outlives one change, a provider, library, data model, pattern or stack, and record it as an ADR or a spec section; asks what only the user knows, recommends the rest.
disable-model-invocation: true
argument-hint: <the decision to settle> [constraints]
---

# Architect

Decide between approaches when the choice will still be true after this change ships, and
write the decision where the next run reads it. `jankolenko-skills:plan` decides how to
change the code. This skill decides which way, and why, before a plan depends on it.

## Inputs

- `decision` — **required.** The choice to settle, as a question: "which cache layer",
  "how sessions are stored", "one error shape across services".
- `options` — approaches already on the table. They enter Step 2 as entries, never as the
  answer.
- `constraints` — the stack in use, house rules, anything ruled out, what earlier runs
  learned.
- `destination` — `adr` (default: the repository's ADR folder, else `docs/adr/`),
  `confluence` with a `page_url`, or `chat`.

## Output

| Field | Contents |
| --- | --- |
| `decision.choice` | The approach chosen, one sentence |
| `decision.rejected` | Each rejected option with the fact that ruled it out |
| `decision.consequences` | What becomes easier, harder or forbidden, and what would reverse it |
| `decision.open` | What the user could not answer, with what would settle it |
| `decision.record` | The file or page section written, or `chat` |

## Step 1 — Sort every question before asking one

Three piles. **Infer** what the code, the manifest, the lockfile and the recorded decisions
already answer: the stack, the platform, a provider already in use. **Ask** only what the
user alone knows: requirements, traffic, budget, compliance, who runs it, taste.
**Recommend** what expertise settles: which library or pattern fits, with its runner-up.
Done when: every open question sits in one pile and the ask pile is short.

> 🛑 **GATE — each question in the ask pile.** Ask through `AskUserQuestion`, one decision
> per call, the plausible answers as options with the recommended one first and its reason
> in the description. A decision the user must own is not made for them because one answer
> looked obvious. Standing rule: refuse rather than guess.

Fold each answer into `constraints`. Done when: the ask pile is empty or `decision.open`
holds what could not be answered.

## Step 2 — Compare on the facts that decide it

Name at least two options that differ in mechanism, the user's and yours. Compare them on
what decides the case, not on a feature list: fit with the stack already in use (reuse
beats a new dependency), the failure modes each carries, the cost to reverse, who has to
maintain it. Check an assumption now when it is cheap, a build, a query plan, a benchmark.
A claim about a library comes from its documentation, read now, not from memory. Take the
simplest option that fully meets the constraints. Done when: `decision.choice` and every
`decision.rejected` entry name the deciding fact.

## Step 3 — Record it

Write the record in the destination's shape:

| Destination | Shape |
| --- | --- |
| `adr` | The repository's existing ADR format, else title, status, context, decision, consequences, under a page |
| `confluence` | One delimited section through `jankolenko-skills:atlassian-confluence`, which owns that write and its gate |
| `chat` | The same five parts inline |

State each consequence as a constraint the next plan inherits. Done when: `decision.record`
names the file or section and its status is `proposed` or `accepted`.

## Notes

- Decides and records. Builds nothing. The plan that follows takes the choice as a
  constraint.
- A decision with one honest option is not a decision: say so in one line and record
  nothing.
