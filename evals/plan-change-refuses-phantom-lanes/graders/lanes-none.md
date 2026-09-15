---
type: regex
target: last_message
match: contains
flags: i
weight: 1
---
(plan\.)?lanes?\b[^\n]{0,80}\b(none|n/a|not applicable|single|one lane|not split|no split|serial)|\bno (independent |separate |parallel )?lanes?\b|\b(single|one) lane\b|too (small|coupled|tightly coupled|intertwined) to (parallelis|parallelize|split)|(does not|doesn't|cannot|can't|shouldn't|should not|won't|will not) (be )?(split|parallel|partition)|not worth (splitting|parallel)
