---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit]
---

The retry backoff in `src/retry.js` should double each time instead of growing by 100ms —
100ms, 200ms, 400ms, 800ms. Make that change and keep everything else as it is. Nothing
else in the repo imports `retry.js`.
