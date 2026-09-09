#!/usr/bin/env bash
# Builds the scratch repository this case runs in. The eval runner executes it in the
# sandbox before the agent's first turn (pass --scaffold), so the prompt carries only the task.
set -euo pipefail

mkdir -p src && \
printf '%s\n' \
'// Five attempts keeps a full retry cycle under a second of waiting, which is the' \
'// figure the request budgets elsewhere were sized against.' \
'const MAX_ATTEMPTS = 5;' \
'' \
'/**' \
' * Calls `fn` until it resolves, up to MAX_ATTEMPTS times.' \
' *' \
' * Backs off linearly between attempts — 100ms, 200ms, 300ms, 400ms — so a caller' \
' * that needs a hard ceiling can add the delays up. See `delayFor`.' \
' */' \
'export async function retry(fn) {' \
'  let lastError;' \
'  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {' \
'    try {' \
'      return await fn();' \
'    } catch (err) {' \
'      lastError = err;' \
'      if (attempt < MAX_ATTEMPTS) await sleep(delayFor(attempt));' \
'    }' \
'  }' \
'  throw lastError;' \
'}' \
'' \
'function delayFor(attempt) {' \
'  return attempt * 100;' \
'}' \
'' \
'const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));' > src/retry.js && \
git init -q . && git add -A && git -c user.email=e@x -c user.name=n commit -qm init && ls src
