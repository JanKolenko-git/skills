---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit]
---

`ConsentModal.jsx` was ported off `legacy-ui` to `modern-ui` last week. Nothing in `src/`
imports `legacy-ui` JavaScript any more, the test suite is green, and the modal renders
correctly.

Drop the `legacy-ui` dependency and remove what it left behind.
