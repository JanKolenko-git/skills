---
name: explain
description: Explain something the user does not understand, code, a principle like hydration, a metric like INP, a header value, a product feature, in plain accurate words grounded in the real code or docs. Use when the user asks what something is or means, how it works, why it behaves that way, or how to do X with Y, however short the question.
argument-hint: <the thing you don't understand> [what you're trying to do with it]
---

# Explain

Most explanations swap one unfamiliar word for five more: "hydration is the process where
client-side JavaScript turns a server-rendered page into an interactive application" is
true and teaches nothing. Never let a word do the work of an explanation. Keep the real
terms, since the reader has to say `LCP` and `Virtual DOM` to colleagues tomorrow, and
spend a clause on what each one is the moment it appears.

## Inputs

- `subject` — **required.** A file path or pasted code, a concept, an acronym, a product
  feature, an error, or a "how do I build X" question.
- `purpose` — optional. What the user is about to do with the understanding: implement,
  debug, decide, review. Shapes what to cover and what to skip.
- `depth` — optional, default working knowledge: enough to use the thing correctly and
  recognise when it breaks.

## Output

| Field | Contents |
| --- | --- |
| `explanation.mode` | `code` · `concept` · `term` · `build` |
| `explanation.body` | The explanation, in the terminal; no files, no artifacts |
| `explanation.analogy` | The everyday-object closer |
| `explanation.sources` | Docs consulted, or `from knowledge` |
| `explanation.uncertain` | Anything stated that was not verified; empty is a valid answer |

## Step 1 — Name the mode, because it sets the length

| Mode | Question shape | Shape of the answer |
| --- | --- | --- |
| `code` | "what does this do" | Read it, then: purpose, the path through it, the surprising part |
| `concept` | "how does X work" | The mechanism as a sequence, what happens in order |
| `term` | "what is LCP" | Short: what it measures, a good number, what moves it |
| `build` | "how do I track X in Y" | The mechanism, then the actual code or config |

## Step 2 — Ground it before writing a word

A named product, API, version or config flag is looked up, because these change between
versions and a wrong property name costs an implementation attempt; record what you read in
`explanation.sources`. A stable fundamental (LCP, hydration, TCP, cache invalidation) comes
from knowledge. `code` mode reads the actual file, never explaining code from its name.

Anything you are not sure of is said plainly in the body, in ordinary words ("I'm not
certain the property is called `timerName`; check the docs before wiring it up"), never
smoothed over with a confident metaphor. A good analogy makes a wrong explanation more
convincing, and the reader will defend the vivid model of something untrue.

## Step 3 — Answer in the first sentence

Lead with what the thing is, in one sentence; the user is stuck mid-task and often that
sentence is all they needed. Then: chronological when there is a sequence; concrete over
abstract (`LCP under 2.5s`, "saves the ~200ms round trip to origin", never "improves
performance"); define on first use in the same breath (`the DOM (the browser's live model
of the page)`); short sentences; and why the mechanism exists, because a mechanism whose
problem you understand is one you can reason about later.

Banned, because each is a word doing an explanation's job: *the process where*,
*leverages*, *orchestrates*, *facilitates*, *seamlessly*, *under the hood*, and any
definition that reuses the word being defined.

## Step 4 — Land the analogy

One or two sentences at the end, once the technical picture is built: everyday physical
objects (skeletons, blueprints, warehouses, post offices), one analogy per explanation, and
half a sentence on where it breaks if that matters. Analogy as the spine of the answer,
naming each step, only when the mechanism is genuinely counter-intuitive: hydration earns
it, "what is INP" does not.

## Step 5 — For `build`, finish the job

A `build` question is an implementation about to happen, so end with the actual snippet,
the real API call or config, plus the one thing most likely to go wrong: a timer that never
fires, a value reported in the wrong unit.

## Notes

- Terminal prose only. No files, no artifacts, no "shall I write this up?".
- Explains; does not build. Once the user wants the change made, that is
  `jankolenko-skills:plan` and the implementation skills.
- A yes/no question gets yes or no first.
