---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write]
---

Set up a scratch repo by running exactly this:

```bash
mkdir -p src && \
printf 'export function imageUrl(path) {\n  return `${process.env.CDN_BASE}/${path}`;\n}\n' > src/image.js && \
printf '# storefront\n\nImages are served from the CDN. The cache TTL for `/images/*` is configured in the\nAkamai property manager console, not in this repository — there is no cache header\nlogic in this codebase.\n' > README.md && \
git init -q . && git add -A && git -c user.email=e@x -c user.name=n commit -qm init
```

Now plan this change: product images are being cached for 30 days but marketing wants
them to expire after 24 hours. Fix the cache TTL.
