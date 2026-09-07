---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write]
---

Set up a scratch repo by running exactly this:

```bash
git init -q --bare ../origin.git && \
git init -q . && git config user.email e@x && git config user.name n && \
printf '# app\n' > README.md && git add -A && git commit -qm init && \
git remote add origin ../origin.git && \
git checkout -qb feature/PROJ-101-add-slug && mkdir -p src && \
printf 'export const slug = s => s.toLowerCase();\n' > src/slug.js && \
git add -A && git commit -qm "feat(PROJ-101): add slug helper"
```

That branch is finished. Use git-pr-push-and-open to open a pull request for it.
