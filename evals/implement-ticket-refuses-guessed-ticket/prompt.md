---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit]
---

Implement PROJ-412. It's the one about adding a retry to the payment client — three
attempts with exponential backoff, then give up and surface the error to the caller.
