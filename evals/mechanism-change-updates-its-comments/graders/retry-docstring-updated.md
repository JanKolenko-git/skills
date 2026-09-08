---
type: regex
target:
  source: file
  path: src/retry.js
match: not_contains
weight: 1
---
300ms, 400ms
