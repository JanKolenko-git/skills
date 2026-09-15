---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit, AskUserQuestion]
---

This directory is my checkout of the jankolenko-skills repo. git-create-branch just built me
`feature/PROJ-101-cart-total-wrong-vat-rounding-p2` from the ticket title "Cart total is
wrong when VAT rounding applies (P2)": it kept the bracketed priority tag as a slug word.
Step 3 says to drop filler and punctuation but says nothing about tags in brackets, so the
tag survives as `p2`. Fix the skill so anything in parentheses or square brackets is dropped
from the slug. I'm going into a meeting now, get that fixed while I'm out.
