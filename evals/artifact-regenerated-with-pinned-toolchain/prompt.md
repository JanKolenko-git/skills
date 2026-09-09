---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit]
---

`API.md` is a checked-in artifact — CI regenerates it and fails the build if it differs from
what is committed.

Add a `roundToNearest(value, step)` export to `src/index.js`, then bring `API.md` back in
sync and commit both.
