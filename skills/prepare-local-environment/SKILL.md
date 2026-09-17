---
name: prepare-local-environment
description: Get a repository running so it can be exercised by hand: work out how it runs, install, build if needed, start the dev server, prove the app rendered. Use when the user asks to run something locally, get it running, set up the local environment, start the dev server, test a branch or PR in the browser, or fix a localhost that spins or 500s.
---

# Prepare Local Environment

Hand back a URL that opens on the thing worth looking at. A listening port is not a working
app: the failure this skill prevents is "it's running on :9000" over a page that spins
forever, because the run checked that the server answered, not that the app rendered.

## Inputs

- `repo` — optional, defaults to the current directory. A project named rather than pathed
  resolves through `jankolenko-skills:find-repository` if installed.
- `target` — optional. What they want to look at: a screen, a route, a scenario. Without
  it, the app's entry point.
- `fresh` — optional, default off. Reinstall from the lockfile and clear build caches;
  worth it after a branch switch that moved dependencies.

## Output

| Field | Contents |
| --- | --- |
| `env.url` | The URL to open, landing on `target`, not the app root |
| `env.command` | What is running, and the directory it runs in |
| `env.stop` | How to stop it |
| `env.evidence` | What proved the app rendered, rather than merely answered |
| `env.workarounds` | What had to be fixed to get here, usually worth committing |
| `env.blocked` | What this environment still cannot do: a missing `.env`, a service behind VPN, an unseeded database |

## Step 1 — Read how this repo runs; never infer it

In order, stopping when you have a command and a port: `.claude/launch.json`; the repo's
own words (`README.md`, `CONTRIBUTING.md`, `CLAUDE.md`); the manifests (`package.json`
scripts, `Makefile`, `Procfile`, `docker-compose.yml`, `pyproject.toml`, `Cargo.toml`,
`go.mod`). In a monorepo the root script fans out to every package: find the package that
changed and read its scripts. The port comes from the script, a config file, `.env` or the
server's first log line. If nothing in the repo says how to run it, stop and ask:
`npx serve` over `dist/` looks like the app and behaves like a museum exhibit.

## Step 2 — Check what the code needs that it does not carry

An `.env.example` with no `.env` beside it, `.nvmrc` or `engines` against the node in the
shell, an `.npmrc` pointing at a private registry with no auth, a database, docker service
or VPN the app reaches for on first paint. Report what is missing rather than papering
over it.

## Step 3 — Clear the ground, then install

Stop whatever is on the port first; an install under a running server leaves it holding
files that no longer exist. Then `npm ci` unless `npm ls --depth=0` shows the install
matches the lockfile: the base moves under a checkout, and a stale install surfaces as a
500 that looks like the app's fault. `npm install` only when this branch edited the manifest
and the lockfile must catch up, and say so. `fresh` also clears `node_modules/.vite`,
`.next`, `.turbo` and `dist`.

## Step 4 — Build only if the run path needs one

Most dev servers compile on demand; SSR services, anything served out of `dist/`, and
Docker paths need a build.

## Step 5 — Start it where you can still read it

Prefer `mcp__Claude_Browser__preview_start` when available: write a `.claude/launch.json`
entry if the repo has none, start by name, and read `preview_logs`. Otherwise background it
and tee the log, then poll until the ready line or the port answers, with a ceiling:

```bash
nohup <the command> > <scratchpad>/dev.log 2>&1 &
```

## Step 6 — Prove the app rendered

A `200` proves a process is listening, not that the app mounted. Fetch the page and look
for content only the app could produce (a heading, a known string, a test id attribute);
an empty root element is a failure dressed as a success. Read the server log, where failed
module resolution, a missing env var and an upstream 500 all serve on through a `200`. In a
browser, read the console; a spinner with no network activity is the endless-spinner case.

Do not report a URL you have not watched render, and do not edit application or server
source to make it render: a component the branch has not written yet is the user's own
work in progress, and your guess at it converts a visible failure into an invisible one.
Say what is missing, offer to write it, and wait.

Done when: `env.evidence` names the content that proved the render.

## Step 7 — Hand over the URL, not the port

The URL lands on `target`; what it cannot carry (a cookie, a seeded row, a two-click path)
is written out as steps. Report the Output fields, including what you changed to get here;
a `.env` created, a cache cleared, a port freed belongs in the repo rather than in your
shell history.

## Notes

- Leave it running; stopping is the user's call, so give them `env.stop`.
- This skill does not drive the app: `/run` launches and exercises one to confirm a change
  works; this one gets it running for the user to look at.
- A generated `.env` holds their values and stays out of the diff; a `.claude/launch.json`
  is usually worth keeping. Standing rule: no secrets in output. A URL carrying a token or
  a session id stays out of the report.
