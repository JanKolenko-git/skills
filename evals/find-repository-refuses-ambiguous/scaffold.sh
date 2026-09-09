#!/usr/bin/env bash
# Builds the scratch repository this case runs in. The eval runner executes it in the
# sandbox before the agent's first turn (pass --scaffold), so the prompt carries only the task.
set -euo pipefail

for r in checkout-web checkout-api; do \
  mkdir -p "repos/$r" && cd "repos/$r" && \
  printf '{ "name": "%s" }\n' "$r" > package.json && \
  printf '# %s\n' "$r" > README.md && \
  git init -q . && git add -A && git -c user.email=e@x -c user.name=n commit -qm init && \
  cd ../..; \
done; ls repos
