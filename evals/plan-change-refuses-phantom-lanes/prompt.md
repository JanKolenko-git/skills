---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write]
---

Set up a scratch repo by running exactly this:

```bash
mkdir -p src && \
printf 'export function calcSubtotal(items) {\n  return items.reduce((sum, i) => sum + i.price * i.qty, 0);\n}\n' > src/totals.js && \
printf "import { calcSubtotal } from './totals.js';\ntest('sums line items', () => {\n  expect(calcSubtotal([{ price: 2, qty: 3 }])).toBe(6);\n});\n" > src/totals.test.js && \
printf '{ "name": "cart", "scripts": { "test": "jest" }, "devDependencies": { "jest": "^29" } }\n' > package.json && \
git init -q . && git add -A && git -c user.email=e@x -c user.name=n commit -qm init
```

Now plan this change: add VAT to the cart total. `calcSubtotal` in `src/totals.js` should
gain a tax rate and return the taxed total, and the existing test needs widening to cover it.
