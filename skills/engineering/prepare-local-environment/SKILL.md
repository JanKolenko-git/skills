---
name: prepare-local-environment
description: Get a repository to the state where you can exercise it by hand — work out how this repo actually runs, install dependencies, build what needs building, start the server, then prove the app really rendered before handing back a URL. Use when the user wants to try a branch in a browser, or says "run this locally", "prepare my local environment", "set this up so I can test it", "start the dev server", "how do I run this", or asks for a link they can open — and any time a change needs looking at by hand rather than by test.
---

# Prepare Local Environment

Hand back a URL that opens on the thing worth looking at. Nothing short of that counts as
done.

A listening port is not a working app. The failure this skill exists to prevent is reporting
"it's running on :9000" over a page that spins forever — which happens because the run
checked that the *server answered*, not that the *app rendered*.

## Inputs

- `repo` — optional, defaults to the current directory. If the user names a project rather
  than a path and **`jankolenko-skills:find-repository` is installed**, resolve it there.
- `target` — optional. What they actually want to look at: a screen, a route, a scenario
  ("the consent modal at en_GB"). It shapes the URL in Step 7; without it, the app's entry
  point.
- `fresh` — optional, default off. Reinstall from the lockfile and clear build caches. Worth
  it after a branch switch that moved dependencies.

## Output

| Field | Contents |
| --- | --- |
| `env.url` | The URL to open — landing on `target`, not just the app root |
| `env.command` | What is running, and the directory it runs in |
| `env.stop` | How to stop it |
| `env.evidence` | What proved the app rendered, rather than merely answered |
| `env.workarounds` | What had to be fixed to get here — usually worth committing |
| `env.blocked` | What this environment still cannot do: a missing `.env`, a service behind VPN, an unseeded database |

## Step 1 — Read how this repo runs; never infer it

In order, stopping when you have a command and a port:

1. **`.claude/launch.json`** — if it exists it already answers this. Use it as written.
2. **The repo's own words** — `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`. These usually name
   both the command and the port, and they are right more often than the manifest is.
3. **Manifests** — `package.json` scripts, `Makefile`, `Procfile`, `docker-compose.yml`,
   `pyproject.toml` / `manage.py`, `Cargo.toml`, `go.mod`.

**In a monorepo the root script is rarely the one you want.** `npm run dev` at the root of a
turbo or nx workspace fans out to every package at once; the server you need is the one
belonging to the package that changed. Find that package first, then read *its* scripts —
they often invoke a framework CLI the root never mentions.

Get the port from the script, a config file, `.env`, or the first line the server logs. Do
not assume 3000.

> 🛑 **GATE:** If nothing in the repo says how to run it, **STOP** and ask. Improvising
> `npx serve` over a `dist/` produces something that looks like the app and behaves like a
> museum exhibit — the user tests it, believes what they see, and the belief is wrong.

## Step 2 — Check what the code needs that the code does not carry

Before installing anything, because these are what turn a clean start into a broken page: an
`.env.example` with no `.env` beside it, `.nvmrc` or `engines` against the node actually in
the shell, an `.npmrc` pointing at a private registry with no auth, a database or docker
service or VPN the app reaches for on first paint.

Report what is missing rather than papering over it. Some of it only the user can supply, and
learning that now is cheaper than learning it from a blank screen in Step 6.

## Step 3 — Clear the ground, then install

Stop whatever is already on the port before installing, in that order. An install that
replaces `node_modules` under a running dev server leaves that server holding files that no
longer exist, and its errors will not look like the cause.

- **`npm ci`** when the lockfile is authoritative. It is the only install that reproduces
  what CI and production see, and the only one to use before measuring anything.
- **`npm install`** when this branch edited the manifest and the lockfile has to catch up —
  then say so, because the lockfile is now part of the diff.
- **`fresh`** additionally clears the caches that survive a dependency change and quietly
  serve stale modules: `node_modules/.vite`, `.next`, `.turbo`, `dist`.

## Step 4 — Build only if the run path needs one

Most dev servers compile on demand, so a build first is wasted minutes. SSR services,
anything served out of `dist/`, and Docker paths do need one. If the repo documents a command
for local work, trust that it does what it needs.

## Step 5 — Start it where you can still read it

If `mcp__Claude_Browser__preview_start` is available, prefer it: write a `.claude/launch.json`
entry if the repo has none, then start by name. The process survives the turn and
`preview_logs` gives you stdout and stderr — which is where the real failure usually is when
the page itself looks fine.

Otherwise background it and tee it somewhere readable:

```bash
nohup <the command> > <scratchpad>/dev.log 2>&1 &
```

A foreground server blocks the turn and dies with it. Do not `sleep` and hope, either — poll
until the server logs its ready line or the port answers, with a ceiling, then read the log.

## Step 6 — Prove the app rendered

The step the skill exists for. A `200` proves a process is listening; it does not prove the
app mounted. In rough order of what actually catches things:

- **Fetch the page and look for content only the app could have produced** — a heading, a
  known string, a `data-auto-id`. An HTML shell with an empty root element is a failure
  dressed as a success.
- **Read the server log.** Failed module resolution, a missing env var, an upstream 500 — a
  server will happily keep serving through all three without changing its status code.
- **Open it, if a browser is available, and read the console.** An uncaught error, or a
  spinner with no network activity behind it, is the endless-spinner case: the page loads,
  the app never finishes.

> 🛑 **GATE:** Do not report a URL you have not watched render. The user's next move is to
> open it and believe it, and a URL handed over on the strength of a status code moves the
> debugging onto them — which is the errand they asked you to run.
>
> Nor does preparing an environment stretch to editing application or server source until
> the page renders. A component the branch has not written yet, a module that does not
> resolve — that is the user's own work in progress, and supplying your guess at it converts
> a visible failure into an invisible one: the page renders, they believe it, and what they
> are looking at is yours. Offering to write the missing piece and waiting is the move;
> writing it and reporting the app as working is not. Say what is missing and let them
> decide.

## Step 7 — Hand over the URL, not the port

Give them the URL that lands on `target`. If getting there needs query parameters, a cookie,
a seeded row or a two-click path, put what you can in the URL and write the rest out as
steps — "open X, click Y" beats "it's on 9000, go find it".

Then report the Output fields, including what you changed to get here. A `.env` you created,
a cache you cleared, a port you freed: the next person hits the same wall, and half of these
belong in the repo rather than in your shell history.

## Notes

- **Leave it running.** Stopping is the user's call; give them `env.stop` and let them.
- This skill does not drive the app. Claude Code's built-in `/run` launches and *exercises*
  one to confirm a change works. Reach for `/run` when you want the agent to check; reach for
  this when the user wants to look.
- Say what you generated to get running rather than quietly committing it. A `.env` holds
  values that are theirs and stays out of the diff; a `.claude/launch.json` is usually worth
  keeping. Either way it is their call, and a URL carrying a token or a session id is a
  secret rather than a convenience — keep that one out of the report entirely.
