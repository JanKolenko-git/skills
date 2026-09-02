---
type: llm
weight: 1
---

This is a two-file change. The skill must produce a plan AND must report that the work
does NOT split into parallel lanes.

PASS requires both:
1. A real plan naming the actual paths `src/totals.js` and `src/totals.test.js`
   (not "the cart logic" or other unnamed generalities), with ordered steps.
2. `plan.lanes` reported as `none` — or an unmistakable statement that the work is
   too small / too coupled to parallelise.

FAIL if the response proposes lanes, parallel workstreams, or fanning out to
subagents for a two-file change. Manufacturing parallelism that isn't there is the
exact failure this case exists to catch.

FAIL if it names no concrete file paths.
