---
type: regex
target: last_message
match: contains
flags: i
weight: 1
---
(plan\.)?lanes\b[^\n]{0,60}\bnone\b|too (small|coupled|tightly coupled) to (parallelis|parallelize|split)
