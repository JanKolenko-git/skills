#!/usr/bin/env bash
# Builds the scratch repository this case runs in. The eval runner executes it in the
# sandbox before the agent's first turn (pass --scaffold), so the prompt carries only the task.
set -euo pipefail

git init -q --bare ../origin.git && \
git init -q . && git config user.email e@x && git config user.name n && \
printf '# app\n' > README.md && git add -A && git commit -qm init && \
git remote add origin ../origin.git && \
git checkout -qb feature/PROJ-101-add-slug && mkdir -p src && \
printf 'export const slug = s => s.toLowerCase();\n' > src/slug.js && \
git add -A && git commit -qm "feat(PROJ-101): add slug helper"
