---
name: explain
description: Explain something the user does not understand — a block of code, a principle like CDN caching or hydration, a metric like LCP/CLS/INP, or how to build a specific thing with a specific product — in plain words that stay technically accurate, grounded in the real code or the real docs, and closed with an everyday analogy. Use whenever the user asks what something is, how something works, why something behaves the way it does, or says they do not get it — including short questions like "what is INP?" and code questions like "what does this file do?". Reach for it even when the question looks answerable in one line, because the reflex answer to those is a definition made of more jargon, which leaves the user exactly where they started.
argument-hint: <the thing you don't understand> [what you're trying to do with it]
---

# Explain

Most explanations fail the same way: they swap one unfamiliar word for five more.
*"Hydration is the process where client-side JavaScript turns a static, server-rendered
HTML page into a fully interactive web application"* is technically true and teaches
nothing — every load-bearing word in it is a word you would have to already know.

This skill's opinion: **never let a word do the work of an explanation.** Keep the real
technical terms — the reader has to say `LCP` and `Virtual DOM` out loud to colleagues
tomorrow — but the moment a term appears, spend a clause saying what it actually *is*.
The enemy is unexplained abstraction, not vocabulary.

## Inputs

- `subject` — **required.** What to explain: a file path or pasted code, a concept, an
  acronym, a product feature, an error, or a "how do I build X" question.
- `purpose` — optional. What the user is about to *do* with the understanding —
  implement it, debug it, decide something, review someone's work. Shapes what to cover
  and what to skip.
- `depth` — optional, default *working knowledge*: enough to use the thing correctly and
  recognise when it breaks. Not a full specification.

## Output

| Field | Contents |
| --- | --- |
| `explanation.mode` | `code` · `concept` · `term` · `build` |
| `explanation.body` | The explanation, in the terminal — no files, no artifacts |
| `explanation.analogy` | The everyday-object closer |
| `explanation.sources` | Docs consulted, or `from knowledge` |
| `explanation.uncertain` | Anything stated that was not verified — empty is a valid answer |

## Step 1 — Name the mode, because it sets the length

| Mode | Question shape | Shape of the answer |
| --- | --- | --- |
| `code` | "what does this do" | Read it, then: purpose, the path through it, the surprising part |
| `concept` | "how does X work" | Mechanism as a sequence — what happens, in order |
| `term` | "what is LCP" | Short. What it measures, what a good number is, what moves it |
| `build` | "how do I track X in Y" | The mechanism, *then the actual code or config* |

Getting this wrong wastes the user's time in both directions: three paragraphs of theory
for `term`, or a one-line definition for `build`.

## Step 2 — Ground it before writing a word

- **Named product, API, version or config flag** (mPulse custom timers, an Akamai cache
  key, a library option) — look it up. These change between versions and a wrong property
  name costs an implementation attempt. Record what you read in `explanation.sources`.
- **Stable fundamental** (LCP, hydration, TCP, cache invalidation) — from knowledge. A
  search here only adds latency.
- **`code` mode** — read the actual file. Never explain code from its name or from what a
  function like it usually does.

> 🛑 **GATE:** A good analogy makes a wrong explanation *more* convincing, not less — the
> reader now has a vivid mental model of something untrue, and will defend it. So anything
> you are not sure of gets said plainly, in the body, in ordinary words: *"I'm not certain
> the property is called `timerName` — check the docs before wiring it up."* Never smooth
> uncertainty over with a confident metaphor.

## Step 3 — Answer in the first sentence

Lead with what the thing *is*, in one sentence, before any build-up. The user is stuck
mid-task; often that sentence is all they needed and the rest is optional reading.

Then the body:

- **Chronological when there is a sequence.** Step 1, Step 2, Step 3 — what actually
  happens, in the order it happens.
- **Concrete over abstract.** Real thresholds (`LCP under 2.5s`), real names, real numbers.
  "Improves performance" says nothing; "saves the ~200ms round trip to origin" says it.
- **Define on first use, in the same breath.** `the DOM (the browser's live model of the
  page)`. One clause, then move on — do not stop to lecture.
- **Short sentences.** One idea each.
- **Say why it exists.** A mechanism whose problem you understand is one you can reason
  about later; one you memorised is one you forget.

Banned outright, because each is a word doing an explanation's job: *the process where*,
*leverages*, *orchestrates*, *facilitates*, *seamlessly*, *under the hood*, and any
definition that reuses the word being defined.

## Step 4 — Land the analogy

Default: **one or two sentences at the end**, once the technical picture is already built.
The analogy makes it stick; it does not carry the explanation.

Escalate to analogy-as-spine — naming each step, like *Step 1: The Mechanical Skeleton
(HTML)* — only when the mechanism is genuinely counter-intuitive and plain steps would
leave the reader asking *but why does it work that way?* Hydration earns it. "What is INP"
does not; forcing a metaphor onto something simple is just noise.

Rules that hold either way: everyday physical objects — skeletons, blueprints, warehouses,
post offices. **One analogy per explanation**; a mixed metaphor is worse than none. And if
the analogy breaks somewhere that matters, say where in half a sentence.

## Step 5 — For `build`, finish the job

A `build` question is an implementation about to happen. Theory alone leaves the user
exactly as blocked as before, so end with the actual snippet — the real API call, the real
config — plus the one thing most likely to go wrong (a timer that never fires, a value
that reports in the wrong unit).

## Notes

- Terminal prose only. No files, no artifacts, no "shall I write this up?" — this is
  unblocking someone mid-task, not producing a document.
- Explains; does not build. Once the user wants the change made, that is `jankolenko-skills:plan-change` and
  the implementation skills.
- When the question was actually a yes/no, answer yes or no first. An explanation nobody
  asked for is a worse failure than one that is slightly too short.
