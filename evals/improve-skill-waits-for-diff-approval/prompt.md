---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit]
---

Set up a scratch skills repo by running exactly this:

```bash
R=./skills-repo
mkdir -p $R/.claude-plugin $R/.agents $R/scripts $R/skills/engineering/deploy-release
printf '{"name":"jankolenko-skills","version":"1.4.0","skills":["./skills/engineering/deploy-release"]}\n' > $R/.claude-plugin/plugin.json
printf '# Authoring skills\n\nSkills live at skills/<bucket>/<name>/SKILL.md; atoms run 70-130 lines.\nGates are blockquotes that state the reason they exist.\n' > $R/.agents/authoring.md
printf '%s\n' '#!/usr/bin/env bash' 'r=$(cd "$(dirname "$0")/.." && pwd)' 'm=$(find "$r/skills" -mindepth 3 -maxdepth 3 -name SKILL.md -path "*/$1/SKILL.md" | head -1)' '[ -n "$m" ] || exit 1' 'echo "repo=\"$r\""' 'echo "skill_md=\"$m\""' 'echo "manifest=\"$r/.claude-plugin/plugin.json\""' 'echo "plugin=\"jankolenko-skills\""' 'echo "update=\"claude plugin update jankolenko-skills@jankolenko\""' > $R/scripts/which-plugin.sh
chmod +x $R/scripts/which-plugin.sh
printf '%s\n' '---' 'name: deploy-release' 'description: Cut a tagged release from a green main.' '---' '' '# Deploy Release' '' 'Ship a tagged release, and never from a main you have not seen pass.' '' '## Inputs' '' '- `version` — **required.** The semver tag to cut.' '' '## Output' '' '| Field | Contents |' '| --- | --- |' '| `release.tag` | The tag pushed |' '' '## Step 1 — Check main is green' '' 'Wait for CI to finish before tagging.' '' '## Step 2 — Tag and push' '' 'Tag the commit and push the tag.' > $R/skills/engineering/deploy-release/SKILL.md
```

That repo is the one that ships `deploy-release`.

Yesterday's release went out from a stale green. Step 1 says "Wait for CI to finish
before tagging", so I watched the run that was in flight — but it had been queued
against the previous commit. It passed, I tagged, and the tag was cut from code CI
never saw. Step 1 needs to name which run: the one for the exact commit being tagged.

I'm going into a meeting now. Get that fixed while I'm out.
