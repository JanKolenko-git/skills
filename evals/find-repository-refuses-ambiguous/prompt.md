---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write]
---

`checkout-web` is the storefront checkout flow; `checkout-api` is the checkout service
backend. Treat the `repos` directory as the only place repositories live.

Use find-repository to work out which repository this task belongs to: "Checkout
total is wrong when a discount code is applied."
