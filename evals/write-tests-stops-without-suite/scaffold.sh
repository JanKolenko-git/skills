#!/usr/bin/env bash
# Builds the scratch repository this case runs in. The eval runner executes it in the
# sandbox before the agent's first turn (pass --scaffold), so the prompt carries only the task.
set -euo pipefail

mkdir -p src && \
printf 'export function slugify(title) {\n  return title.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-");\n}\n' > src/slugify.js && \
printf '{ "name": "blog", "version": "1.0.0" }\n' > package.json && \
git init -q . && git add -A && git -c user.email=e@x -c user.name=n commit -qm init
