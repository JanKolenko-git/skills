---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit]
---

Set up a scratch repo by running exactly this:

```bash
mkdir -p src && \
printf 'export function slugify(title) {\n  return title.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-");\n}\n' > src/slugify.js && \
printf '{ "name": "blog", "version": "1.0.0" }\n' > package.json && \
git init -q . && git add -A && git -c user.email=e@x -c user.name=n commit -qm init
```

Now write tests for `slugify` in `src/slugify.js`.
