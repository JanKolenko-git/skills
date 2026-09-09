---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write]
---

Plan this change: add VAT to the cart total. `calcSubtotal` in `src/totals.js` should
gain a tax rate and return the taxed total, and the existing test needs widening to cover it.
