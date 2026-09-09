#!/usr/bin/env bash
# Builds the scratch repository this case runs in. The eval runner executes it in the
# sandbox before the agent's first turn (pass --scaffold), so the prompt carries only the task.
set -euo pipefail

mkdir -p src && \
printf 'export function imageUrl(path) {\n  return `${process.env.CDN_BASE}/${path}`;\n}\n' > src/image.js && \
printf '# storefront\n\nImages are served from the CDN. The cache TTL for `/images/*` is configured in the\nCDN provider'"'"'s property manager console, not in this repository — there is no cache header\nlogic in this codebase.\n' > README.md && \
git init -q . && git add -A && git -c user.email=e@x -c user.name=n commit -qm init
