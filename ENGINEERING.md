# Engineering rules

Cross-cutting rules for the **code the skills produce**, read before a skill changes a work
repo. No skill restates these; a rule only one task cares about stays in that SKILL.md.

## How an entry earns its place

**Rules** — one observed failure, in a real run, that the rule would have caught. Added
through `jankolenko-skills:record-engineering-rule`. **Baseline** — established practice
with a named source (Power of 10, a published style guide, a convention a large codebase
visibly holds). No source outside this file, no entry. A Baseline rule a run later violates
is promoted to Rules with the evidence; a rule that proved wrong is deleted.

## What a rule may name

Only what would hold in a repository you have never seen: the **shape** of the failure, never
a repository, ticket, pull request, commit, person or private package. A rule that holds only
in repositories you can list belongs in that repository's own `CLAUDE.md`.
`jankolenko-skills:record-engineering-rule` decides which.

---

# Rules

_Observed. Each entry names the shape of the run that bought it._

## Simple code beats a marginal improvement

```ts
// no — a one-shot helper grows a follow loop so a late-mounting section can move under it
export function scrollToElement(target, offset) {
  /* 36 lines → 154: stop rules, a time bound, four callers wired in to cooperate */
}

// yes — the helper stays one-shot; the late section keeps its box and lazy-loads inside it
<Section style={{ minHeight }}><LazyContent /></Section>
```

Code is paid for on every later change, so each part of a change has to earn its lines. Put
a number on what a part buys (bytes, milliseconds, the share of users affected) before
building it; small next to its code means drop the part. Three tells that a part is not
earning them: constants, coupling comments and specs whose only job is to keep it correct;
simple, shared code from another concern that must get complicated for it to work; fix
rounds that each add a special case. At a tell, stop adding: find the angle where the simple
code keeps working (another layer, another owner, a stable box), or take the part and its
number to the user.

Exception: the simple code was wrong for every caller; then fix it as its own change.

_Source: observed — in one change, a responsive-image tweak worth 20–35 KB on some desktop
screens collected constants, comments and a spec before it was dropped, and a deferred mount
grew a 36-line scroll helper to 154 lines over three fix rounds before it was reverted._

## Reuse the name a thing already has; give a new one meaning

```ts
const requestIdleCallback = window.requestIdleCallback; // yes
const requestIdle = window.requestIdleCallback; // no

const order = getOrder(); // yes
const data = getOrder(); // no
```

Keep the name something else chose: a renamed alias breaks the link to its documentation and
gives the reader a second name for one thing. Rename only when the new name carries
information the old one lacks, or a collision forces it. Name what you invent by its meaning:
`data`, `info`, `item`, `result`, `helper` describe a shape the code already shows, not the
domain concept the reader has to reconstruct.

Exception, second half only: genuinely generic code, where a `map` helper's `item` really is
any item.

_Source: first half observed (this file's founding entry); second half Ousterhout, ‹A
Philosophy of Software Design› §14._

## A stylesheet is unused only if the rendered markup says so

```scss
.app {
  // no — the JS that imported the barrel is gone, so the sheet must be dead too
- @import '@design-system/collection-v6/css';
  @include meta.load-css('@design-system/collection/style.css');
}
```

```js
// yes — ask the rendered screen which classes it uses, then diff the sheets
const used = new Set([...document.querySelectorAll('*')].flatMap((el) => [...el.classList]));
```

Removing a stylesheet passes types, lint, tests and the build, because a class name and a
rule are coupled by a string the browser resolves at runtime. The component whose JS you
deleted is not the only thing the sheet dressed: ask the rendered DOM which classes it uses,
in every state, and diff the sheets. Tell: `getComputedStyle(el).appearance === 'auto'` on a
control that should be custom-styled.

Exception: classes confirmed absent from the rendered DOM in every state.

_Source: observed — a design system's stylesheet dropped with its JavaScript barrel cost ten
classes their rules; the component checked had been ported, the controls inside it had not._

## Generate an artifact with the toolchain the repo pins

```bash
node -v                # v24.18.0, while .nvmrc says 20.19.2
npm install            # no — 1008 lockfile lines of npm-11 re-hoisting

nvm use                # 20.19.2
npm install            # yes — 21 lines, one version actually changed
```

A generator's output differs between versions; on the wrong one it produces an artifact that
is valid, passes tests, and is wrong in bulk, and the only tell is a diff far larger than the
change deserves. Read the pin (`.nvmrc`, `.tool-versions`, `engines`) and match it before the
generator runs.

Exception: a repo that pins nothing, and generators whose output does not vary by version.

_Source: observed — a lockfile regenerated under a newer Node than the repo pinned rewrote
1008 lines for one changed package; under the pin, 21._

## Generated artifacts ship in the commit that changed their source

```
src/lib/index.ts   + export function startInteractionTimer(…)
API.md               unchanged                                     // no

src/lib/index.ts   + export function startInteractionTimer(…)
API.md             + export function startInteractionTimer(…)      // yes
```

Anything derived from a source you changed (an API report, a lockfile, a snapshot, a
generated client) is part of that change; the moment the two disagree, the artifact lies to
every reader. These checks hide behind a separate script (`document`, `generate`,
`snapshot -u`) a scoped verification never runs, so find out what a package regenerates
before calling a change verified.

Exception: artifacts the repo deliberately does not commit. When regeneration needs an
environment you cannot run, say the artifact is stale; never commit a stale one silently.

_Source: observed — two new exports left a library's generated API report stale; verification
had been scoped to the two changed files._

## Parse at the boundary; trust the types inside it

```ts
const user = await res.json() as User            // no — a cast is a wish, not a check
const user = UserSchema.parse(await res.json())  // yes

if (strategy === 'when-near-viewport') defer()   // no — a host still sending the old
                                                 //   `{ type: … }` shape matches nothing
                                                 //   and loads eagerly, in silence
if (strategy !== 'immediate' && strategy !== 'when-near-viewport') {
  warn(`unrecognised strategy`, strategy)        // yes — the boundary says so
}
```

TypeScript checks what you wrote, not what arrives: every API response, env var, URL param,
`postMessage` payload and file read enters as `unknown` wearing a type you asserted, and
`as` tells the compiler to stop asking. Validate once where data enters, then trust the
types. A library's public prop or option is a boundary too: JavaScript hosts keep sending
the shape you stopped accepting.

Exception: internal calls already behind a validated boundary.

_Source: Power of 10 §5 and §7. Promoted when a library option went from object to string as
a minor and a JavaScript host still passing the object lost its deferral silently in
production._

## Comments explain why, not what, in two sentences at most

```ts
// increment the counter
count++;                                                // no — the code already said this

/**
 * Rendered width of a gallery image. From 960px the grid is two columns beside the
 * sidebar: (min(1920px, 100vw) - sidebar) / 2, with the sidebar at 370/434/480px …
 * (nine more lines: a browser quirk, an assumption, the layout that would break it)
 */
const sizes = '(min-width: 1440px) calc(50vw - 240px)'  // no — 240 is a name the
                                                        //   comment is standing in for

const SIDEBAR_WIDTH_PX = { desktop: 480 }
// Ignores the scrollbar on purpose: Chrome counts an upscaled image at its file size
// for LCP, so an understated slot costs more than an overstated one.
const sizes = `(min-width: 1440px) calc(50vw - ${SIDEBAR_WIDTH_PX.desktop / 2}px)` // yes
```

The compiler documents what; a name documents a value. A comment is at most two short
sentences, a line each, carrying only what neither can: the constraint that forced this
shape, the bug that made the obvious version wrong, the check that looks redundant and is
load-bearing. One that wants a paragraph stands in for a name the code lacks, a bare number,
an unnamed step, an assumption nothing asserts; name it in the code and keep the sentence
that is left. Say a reason once, where it lives, a pointer at most at the call site.

Exception: a docblock on a library's published surface may say what it does, still in two
sentences.

_Source: Google, Apple and kernel style guides converge. Sharpened when a rationale copied to
three call sites read as leftover; promoted when a twelve-line comment spelled out widths the
code kept as bare numbers and review asked for names._

## A comment that states a behaviour is checked like the code it describes

```ts
// The observer below catches any early scroll a moment later.
await waitForLayoutToSettle();          // no — nothing is observing during this wait
await waitForViewport(placeholder);

// Nothing observes until layout settles, so an early scroll gets no head start.
// Accepted: observing sooner would trust geometry that is still changing.
await waitForLayoutToSettle();          // yes — the cost is named, not denied
await waitForViewport(placeholder);
```

A comment survives every automated check and is trusted because it explains; when it is
wrong, the next reader reasons from it and nothing fails. When a mechanism moves, grep for
its old name and its old story; when a comment says a case is handled, find the line that
handles it. A comment you cannot point at code for is a guess.

Exception: a comment about the world outside the code (a browser quirk, a measured latency,
a vendor's contract). Date it or cite it.

_Source: observed — one change carried three comments describing mechanisms the code no
longer had; each was caught by a different reader, none by the author._

## An edit is verified by reading it back, not by the tool that applied it

```bash
python3 patch.py                  # prints "patched", exits 0
git commit -m "fix assertion"     # no — nothing has looked at the result

python3 patch.py
git diff -- spec.ts               # yes — the change, not the report of one
```

A patch script, a `sed`, a codemod: each reports its own success and each can succeed while
changing nothing. The exit code is a fact about the tool; the diff is the fact about the
code. Read the diff of every file the tool touched, hardest where nothing else will look: a
test the session cannot run, a config no build loads, a comment.

Exception: an edit followed by a check that exercises it (the test that now passes, the build
that compiles). The check is the read-back.

_Source: observed — a patch script asserted the old block was present, never replaced it and
printed "patched"; the error shipped in the first push._

---

# Baseline

_Sourced. Each entry names where the practice comes from: a published source, or a convention
a large codebase visibly holds, described but not named._

## Every loop, retry and poll carries a bound

```ts
while (!done) { … }                                        // no
for (let page = 0; page < MAX_PAGES && !done; page++) { }  // yes

await fetch(url)                                           // no
await fetch(url, { signal: AbortSignal.timeout(5_000) })   // yes
```

An unbounded loop waits on a condition that may never arrive and fails by hanging: no stack
trace, no log line. A bound turns that into a failure with a message. Name the constant;
`MAX_PAGES` says what it protects, `50` does not.

Exception: a genuine event loop or long-lived consumer, whose shutdown path is then explicit.

_Source: Power of 10 §2._

## Every result is checked; every promise is awaited or explicitly handled

```ts
savePreferences(prefs); // no — a rejection here crashes the process
void savePreferences(prefs); // no — `void` silences the linter, not the bug
await savePreferences(prefs); // yes
savePreferences(prefs).catch(reportFailure); // yes, when the caller must not wait

const res = await fetch(url); // no — res.ok never consulted
if (!res.ok) throw new HttpError(res.status); // yes
```

A floating promise surfaces with no stack pointing at its cause, often in another tick,
sometimes as a process exit; an unchecked `res.ok` turns a 500 into a type error three layers
away. `.catch()` is an answer; `void` documents that you looked at the linter.

Exception: fire-and-forget telemetry, which still gets a `.catch()`.

_Source: Power of 10 §7; `no-floating-promises: "error"` in a production front-end._

## Strict from the first commit; a suppression carries its reason

```ts
// @ts-expect-error                              // no — reason-free
// eslint-disable-next-line                      // no

// @ts-expect-error — upstream types omit the `cause` field, fixed in v5 (#4412)
…                                                // yes
```

A suppression is a claim, and a claim needs a reason a later reader can check and delete; a
reason-free one is indistinguishable from a mistake and outlives the problem by years. New
code compiles clean under the repo's strictest setting from its first commit. Never loosen
`tsconfig` to make a change compile.

_Source: Power of 10 §10; `strict: true` in a large TypeScript codebase._

## Errors are typed, narrowed, and never silently swallowed

```ts
try { … } catch (e: any) {
  console.log(e.message)                     // no — swallowed; execution continues on a lie
}

try { … } catch (e) {                        // `e` is `unknown` under strict
  if (isAbortError(e)) return null           // yes — narrowed, then handled
  throw new UploadError(`upload failed for ${id}`, { cause: e })
}
```

A log-only catch turns a failure into wrong behaviour that keeps running, at the one point
with enough context to say something useful. Catch to handle: recover, or rethrow with more
context and `{ cause }`. Throw `Error` subclasses, never strings; only a real `Error` carries
a stack.

Exception: a cleanup path in a `finally`, where a secondary failure must not mask the
original. Say so in a comment.

_Source: a large TypeScript codebase — 254 catches typed `unknown`, one `Error` hierarchy._

## Return early; keep the happy path at the left margin

```ts
if (user) { if (user.active) { if (hasQuota(user)) { return grant(user); } } } // no
return null;

if (!user) return null; // yes
if (!user.active) return null;
if (!hasQuota(user)) return null;
return grant(user);
```

Every level of indentation is a condition the reader holds until the closing brace, and the
actual work lands furthest from the margin. Guards make the failure cases enumerable, each
readable and testable alone.

Exception: none worth stating. Guards outnumbering the work means the function does two jobs.

_Source: Linux kernel, Go and Google style guides converge here._

## A function fits on one screen

A function you cannot see at once is one nobody verifies: reviewers scroll, then trust. Length
is a symptom of several ideas never named; extract the ideas rather than splitting to a
threshold, which is why this rule states no number.

Exception: a flat exhaustive `switch`, a config literal, a generated mapping.

_Source: Power of 10 §4 (which does state one: ~60 lines)._

## Wait for the third occurrence before abstracting

```ts
function render(item, opts) {
  if (opts.isCard) …                   // no — flags accreting on a premature shared path
  if (opts.isRow && !opts.compact) …
}
```

Two similar blocks are a coincidence; the third shows which parts vary, which is the question
an abstraction has to answer. Abstracting at two guesses the axis, and a wrong abstraction
hides the repetition behind a function that grows a flag, then another; a parameter that
exists only to select behaviour is the tell. Generated code pattern-matches on shape, so this
binds hardest there.

Exception: a contract you already know — an interface a third party defines, a boundary the
architecture requires.

_Source: the rule of three (Fowler, ‹Refactoring›)._

## Export by name, not by default

```ts
export default function parseManifest() { … }   // no
export function parseManifest() { … }           // yes

import parse from './manifest'                   // no — importer invents the name
import { parseManifest } from './manifest'       // yes
```

A default export has no name at its definition site, so every importer invents one: grep finds
the definition and none of the call sites, and a rename has no shared symbol to work on. This
is **Reuse the name a thing already has**, one level up.

Exception: frameworks that require it — a Next.js page or route, a config file loaded by
convention.

_Source: Google TypeScript Style Guide; a large TypeScript codebase — 4702 named exports to
138 default._

## The change includes the deletion

```ts
export function formatPrice(v: number) { … }                  // old, still exported
export function formatPriceV2(v: number, c: Currency) { … }   // no — both are live now
```

Replacing something means removing what it replaced: the commented-out block, the export with
no importer, the flag branch nobody can reach, the helper whose last caller left in this diff.
Version control remembers; commented-out code is a question the next reader cannot answer.
Generated code adds far more readily than it removes, so a diff that only grows gets a second
look.

Exception: a deliberate deprecation window, with a dated removal note and a replacement.

_Source: convergent across large-codebase review practice (Google, Meta)._

## A new dependency is a liability you are choosing

```ts
import { format } from "date-fns";
format(d, "dd/MM/yyyy"); // ~20kB shipped to render one date

new Intl.DateTimeFormat(locale).format(d); // yes — platform, zero bytes, localised
```

A dependency is a supply-chain surface, an upgrade obligation, a bet on somebody else's
maintenance and, on the client, bytes on the critical path. Before adding one, answer in the
PR what it costs to ship, what happens when it goes unmaintained, and how much of it you use.
Reach for the platform first: `Intl`, `URL`, `structuredClone`, `AbortSignal.timeout`.

Exception: cryptography, time zones, and anything with a specification longer than this file.

_Source: convergent across Google, Apple and Meta dependency review._

## Separate the decision from the action

```ts
async function cancel(id: string) {          // no — decision and I/O in one function
  const sub = await db.load(id)
  if (sub.endsAt < new Date()) return
  await db.update(id, { cancelled: true }); await email.send(…)
}

function decideCancellation(sub: Sub, now: Date): CancelAction { … }  // yes — pure
async function cancel(id: string) {                                   // yes — thin shell
  await apply(decideCancellation(await db.load(id), new Date()))
}
```

Logic tangled with I/O can only be tested through that I/O, so the interesting branches go
untested. Pull the decision out as a function of its arguments, `now` included: a function
that reads the clock has a hidden input no test can vary. The shell that remains is thin
enough to check by reading.

Exception: code that is genuinely all action — a migration, a thin adapter.

_Source: Gary Bernhardt, "Boundaries" (2012) — functional core, imperative shell._

---

## What deliberately is not here

Test structure, commit messages, branch naming and whether a change should exist belong to
the skills that own them (`test`, `git-commit`, `git-create-branch`, `plan`
and `check`). Considered and rejected, so they are not re-proposed: declare at
narrowest scope (the linter covers it), formatting (Prettier enforces it), thread a
cancellation signal (promote it if a run gets bitten), make invalid states unrepresentable.
Power of 10 §1, §3, §8 and §9 have no honest analogue in TypeScript.
