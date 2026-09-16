---
type: regex
target:
  source: file
  path: src/constants.ts
match: not_contains
weight: 1
---
\b(?:720|240|217|185)px\b|\b(?:720|240|217|185)\s*[,}\]]
