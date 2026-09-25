# Environment: the long form

Read when Step 2 finds no run path, Step 3's install or build fails, or Step 4's page spins,
500s or renders empty. Every rule here exists because a run once reported a URL over a page
that never rendered.

## Where the run command lives

`.claude/launch.json` first, then the repo's own words, then the manifests. The root script
of a monorepo fans out to every package: run the package the diff touched, from its own
scripts. The port comes from the script, a config file, `.env` or the server's first log
line. Nothing in the repo says how to run it: stop and ask. `npx serve` over `dist/` looks
like the app and behaves like a museum exhibit.

## What the code needs that it does not carry

- An `.env.example` with no `.env` beside it; a generated `.env` holds the user's values and
  stays out of the diff.
- `.nvmrc`, `.tool-versions` or `engines` against the node in the shell: match the pin before
  any install, or the lockfile rewrites itself in bulk.
- An `.npmrc` pointing at a private registry with no auth in the shell.
- A database, docker service or VPN the app reaches for on first paint.

Report each in `walkthrough.blocked`; a run that papers over one hands back an environment
that lies about what it can show.

## Install and build

Stop whatever holds the port first; an install under a running server leaves it holding
files that no longer exist. `npm ci` unless `npm ls --depth=0` shows the install matches the
lockfile: the base moves under a checkout, and a stale install surfaces as a 500 that looks
like the app's fault. `npm install` only when this branch edited the manifest and the
lockfile must catch up, and say so. `fresh` also clears `node_modules/.vite`, `.next`,
`.turbo` and `dist`. Most dev servers compile on demand; SSR services, anything served out
of `dist/`, and Docker paths need a build.

## Start where you can still read it

`mcp__Claude_Browser__preview_start` when available: write a `.claude/launch.json` entry when
the repo has none, start by name, read `preview_logs`. Otherwise:

```bash
nohup <the command> > <scratchpad>/dev.log 2>&1 &
```

then poll until the ready line or the port answers, with a ceiling, and read the log.

## Tells that the app did not render

- A `200` with an empty root element: the bundle failed before mounting; the server log has
  the failed module resolution or the missing env var.
- A spinner with no network activity: the app is waiting on something it never requested,
  usually a failed import or an env var read as `undefined`.
- An upstream 500 served through a `200`: the page shell rendered and the data call failed;
  the browser console and the network tab name the endpoint.
- Content the app could not have produced (a directory listing, a default index page): the
  wrong thing is on the port.

Never edit application or server source to make it render. A component the branch has not
written yet is the user's own work in progress; your guess at it converts a visible failure
into an invisible one. Say what is missing, offer to write it, and wait.
