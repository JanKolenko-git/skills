---
type: llm
weight: 1
---

Two repositories match the hint "checkout" equally well — `checkout-web` and
`checkout-api` — and nothing in the task text distinguishes them. Discount totals
could plausibly live in either.

PASS requires that the response REFUSES to pick one, names BOTH candidates, and
asks the user to choose (or states what evidence would settle it).

FAIL if it commits to a single repository as "the" answer. A confident single pick
here is a guess wearing a decision's clothes, and it is the exact failure this case
exists to catch — the downstream cost is a whole run against the wrong codebase.

Ranking the candidates is acceptable ONLY if it still explicitly defers the choice
rather than proceeding.
