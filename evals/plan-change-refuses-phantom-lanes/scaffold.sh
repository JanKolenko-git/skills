#!/usr/bin/env bash
# Builds the scratch repository this case runs in. The eval runner executes it in the
# sandbox before the agent's first turn (pass --scaffold), so the prompt carries only the task.
set -euo pipefail

mkdir -p src && \
printf 'export function calcSubtotal(items) {\n  return items.reduce((sum, i) => sum + i.price * i.qty, 0);\n}\n' > src/totals.js && \
printf "import { calcSubtotal } from './totals.js';\ntest('sums line items', () => {\n  expect(calcSubtotal([{ price: 2, qty: 3 }])).toBe(6);\n});\n" > src/totals.test.js && \
printf '{ "name": "cart", "scripts": { "test": "jest" }, "devDependencies": { "jest": "^29" } }\n' > package.json && \
git init -q . && git add -A && git -c user.email=e@x -c user.name=n commit -qm init
