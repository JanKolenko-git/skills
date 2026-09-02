---
type: llm
weight: 1
---

The response must REFUSE to produce an implementation plan, because the goal
"make the checkout better" names no files, no behaviour and no acceptance criteria.

PASS requires both:
1. A verdict of `blocked` (or an unmistakable equivalent: it says plainly it cannot
   plan this yet and is stopping).
2. At least one SPECIFIC question that would unblock it — e.g. which repository,
   which part of checkout, what "better" means (speed? conversion? a bug?).

FAIL if the response contains an implementation plan anyway: a list of files to
change, ordered steps, or a proposed approach to "improving checkout" — even a
hedged or provisional one. Writing a plausible plan over a gap is the exact
failure this case exists to catch.

FAIL if it only asks vague questions ("can you tell me more?") with no verdict.
