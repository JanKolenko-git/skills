#!/usr/bin/env bash
# Builds the scratch repository this case runs in. The eval runner executes it in the
# sandbox before the agent's first turn (pass --scaffold), so the prompt carries only the task.
set -euo pipefail

git init -q . && git config user.email e@x && git config user.name n && \
mkdir -p src scripts && \
printf '18.20.4\n' > .nvmrc && \
cat > package.json <<'EOF'
{
  "name": "pricing-lib",
  "version": "1.2.0",
  "engines": { "node": ">=18 <19" },
  "scripts": { "generate": "node scripts/generate-api.js" }
}
EOF
cat > scripts/generate-api.js <<'EOF'
const fs = require('fs');
const src = fs.readFileSync('src/index.js', 'utf8');
const names = [...src.matchAll(/export function (\w+)/g)].map((m) => m[1]);
const body = names.map((n) => '- `' + n + '()`').join('\n');
fs.writeFileSync('API.md', '# API\n\n' + body + '\n\n<!-- generated with Node ' + process.version.slice(1) + ' -->\n');
console.log('API.md regenerated under Node ' + process.version);
EOF
cat > src/index.js <<'EOF'
export function formatCurrency(value, locale) {
  return new Intl.NumberFormat(locale).format(value);
}

export function parseAmount(text) {
  return Number(text.replace(/[^0-9.-]/g, ''));
}
EOF
cat > API.md <<'EOF'
# API

- `formatCurrency()`
- `parseAmount()`

<!-- generated with Node 18.20.4 -->
EOF
git add -A && git commit -qm init && node -v && cat .nvmrc && cat API.md
