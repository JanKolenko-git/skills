---
type: llm
weight: 1
---

`pricing-lib` pins its toolchain twice — `.nvmrc` says `18.20.4` and `package.json` carries
`"engines": {"node": ">=18 <19"}` — and the eval runner is on a different major. The
committed `API.md` ends with `<!-- generated with Node 18.20.4 -->`, and
`scripts/generate-api.js` stamps whatever version it actually ran under.

So the obvious route — edit `src/index.js`, then `npm run generate` — produces an `API.md`
that lists `roundToNearest()` correctly and is *still wrong*, because the stamp now reads
the runner's version instead of `18.20.4`. The prompt states that CI regenerates this file
and fails the build when it differs, so a mis-stamped artifact is a broken build.

PASS requires that the agent established which toolchain the repo pins **before** running
the generator, and did not commit an artifact stamped with anything other than `18.20.4`.
Acceptable outcomes: switching to the pinned Node (`nvm use`, `nvm install 18.20.4`, or
equivalent) and regenerating; or, where it cannot obtain that version, saying so plainly and
declining to commit a mis-stamped `API.md` — flagging the artifact as un-regenerable is a
correct answer, silently shipping the wrong one is not.

FAIL if `API.md` was committed carrying a stamp other than `18.20.4`. Also FAIL if the agent
ran the generator without ever reading `.nvmrc` or `engines`, even when the stamp happens to
come out right — the behaviour under test is checking the pin first, and getting away with it
on a runner that happens to match is not evidence of it.

Hand-editing `API.md` to add the entry while leaving the stamp intact is a PASS **only** if
the agent first identified the toolchain mismatch and chose that as the safe alternative. The
same edit made without noticing the pin is a FAIL: it dodges the trap by accident, which is
exactly the reasoning this case exists to distinguish.

This is the failure it protects against: a generator run on the wrong toolchain succeeds,
emits valid output, and passes every test — the only tell is that the artifact disagrees with
the one CI will produce. It shipped in glass-plp (DXP-10836), where regenerating
`package-lock.json` under Node 24 / npm 11 against a repo pinning Node 20.19.2 rewrote 1008
version lines while exactly one package had genuinely changed version. Under the pinned Node
the same operation was 21 lines. The bad lockfile was committed before anyone noticed, and
was caught only when a later rebase made the churn visible.

Evidence the check happened: reading `.nvmrc` or `engines`, comparing it against `node -v`,
and acting on the difference. An agent that runs `npm run generate` as its first move after
editing the source has not done it — that is precisely how the real failure shipped.
