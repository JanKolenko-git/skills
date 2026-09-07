---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write]
---

Set up two scratch repos by running exactly this:

```bash
for r in checkout-web checkout-api; do \
  mkdir -p "repos/$r" && cd "repos/$r" && \
  printf '{ "name": "%s" }\n' "$r" > package.json && \
  printf '# %s\n' "$r" > README.md && \
  git init -q . && git add -A && git -c user.email=e@x -c user.name=n commit -qm init && \
  cd ../..; \
done; ls repos
```

`checkout-web` is the storefront checkout flow; `checkout-api` is the checkout service
backend. Treat the `repos` directory as the only place repositories live.

Now use find-repository to work out which repository this task belongs to: "Checkout
total is wrong when a discount code is applied."
