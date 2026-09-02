# Engineering rules

Cross-cutting rules for the **code the skills produce** — as opposed to `.agents/authoring.md`,
which governs how the SKILL.md files themselves are written. Different audience, different
moment: this file is read when a skill is about to change a work repo.

Every skill inherits these and none of them restates them. A rule only one task cares about
stays in that task's own SKILL.md.

## How an entry earns its place

Entries arrive one of two ways, and each one says which.

**Rules** — one observed failure, in a real run, that this rule would have caught. These are
the expensive ones, bought with a bug. Add through `record-engineering-rule`, naming the run.

**Baseline** — established practice with a named source: Power of 10, a published style guide
from a team that maintains code at scale, or a convention this repo's own code already holds
across a large codebase. No speculative style preferences. If no source outside this file
believes it, it does not go in — that is what keeps the file short enough to actually be read.

A Baseline rule that a real run later violates gets **promoted to Rules** with the evidence.
That promotion is the point of the split: it records which rules have already cost us
something, so the next reader knows where the sharp edges actually are.

Deleting a rule that proved wrong is as valid as adding one. A rulebook that only grows is
one nobody trusts.

---

# Rules

_Observed. Each entry names the run that bought it._

## Reuse the name a thing already has; give a new one meaning

Two halves of one rule, and they never conflict: the first governs a name something else
chose, the second a name you choose.

**When you bind something that already has a name, keep it.**

```ts
const requestIdleCallback = window.requestIdleCallback; // yes
const requestIdle = window.requestIdleCallback; // no
```

A renamed alias breaks the link between the code and its documentation. Nobody greps
`requestIdle` while reading MDN, and the next reader has to carry a second name for a thing
that already had one. The rule binds hardest on standard Web and Node APIs, then on symbols
exported by dependencies, then on names the repo already uses for the same concept.

Rename only when the new name carries information the old one does not — a real narrowing
(`onIdle` for a callback prop), or a collision you are forced to break.

**When you invent a name, name the thing by meaning.**

```ts
const order = getOrder(); // yes
const data = getOrder(); // no

const user = { name: "John", lastname: "Doe" }; // yes
const data = { name: "John", lastname: "Doe" }; // no
```

`data`, `info`, `item`, `result`, `manager`, `helper` — each describes a value's shape or
its role in the machine, and the code already shows both. What it does not show is which
of your domain's concepts this actually is, so the reader reconstructs that on every read.
A name is the cheapest documentation there is, and the only kind that travels with the
value.

Exception, second half only: genuinely generic code. A `map` helper's parameter is `item`
because it really is any item; inventing a domain name there would be a lie.

_Source: first half observed — this file's founding entry. Second half: Ousterhout, ‹A
Philosophy of Software Design› §14; Kernighan & Pike, ‹The Practice of Programming› §1 —
surfaced by ‹7 Coding Laws of Senior Developer› (law 2)._

## Generated artifacts ship in the commit that changed their source

```
src/lib/index.ts   + export function startInteractionTimer(…)
API.md               unchanged                                     // no

src/lib/index.ts   + export function startInteractionTimer(…)
API.md             + export function startInteractionTimer(…)      // yes
```

Anything derived from a source you just changed — an API report, a lockfile, a snapshot,
a generated client, a `.d.ts` baseline, a checked-in schema — is part of that change, not
a follow-up. The generator is the source of truth for the artifact; the moment the two
disagree, the artifact is lying to every reader who trusts it more than they trust the
diff.

These are the checks most easily missed, because they are usually not what a test failure
or a linter reports. They live behind a separate script — `document`, `generate`,
`snapshot -u` — that a scoped verification run never reaches. Find out what a package
regenerates *before* claiming a change to its public surface is verified.

Exception: artifacts a repo deliberately does not commit (gitignored build output). And
when regeneration needs an environment you cannot run, say the artifact is stale and why —
never commit a stale one silently.

_Source: observed — adding two exports to `@sole/analytics` (DXP-10836) left `API.md`
unregenerated, which the repo's API Extractor check would have failed. Verification had
been scoped to the two changed files, so the package's own `document` script never ran;
review caught it._

---

# Baseline

_Sourced. Each entry names where the practice comes from._

## Every loop, retry and poll carries a bound

```ts
while (!done) { … }                                        // no
for (let page = 0; page < MAX_PAGES && !done; page++) { }  // yes

await fetch(url)                                           // no
await fetch(url, { signal: AbortSignal.timeout(5_000) })   // yes
```

An unbounded loop is fine right up until the condition it waits on never arrives — a
paginated API that keeps handing back a cursor, a poll whose target never turns healthy,
a retry against an endpoint that is simply down. Then it is not a bug that fails, it is a
bug that _hangs_: no stack trace, no error, no log line, just work that never returns.
A bound turns that into a real failure with a real message.

The bound is a constant with a name, not a magic number at the call site. `MAX_PAGES`
tells the next reader what the limit protects; `50` does not.

Exception: a genuine event loop or long-lived consumer, whose termination is external —
a signal, a closed queue. Make that shutdown path explicit rather than implying it.

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

A floating promise is the one mistake in async code that gets _worse_ the further it
travels: the failure surfaces with no stack pointing at the code that caused it, often
in an unrelated tick, sometimes as a process exit. An unchecked `res.ok` is the same
shape — a 500 parsed as JSON becomes a confusing type error three layers away.

`.catch()` is a real answer, `void` is not. `void` documents that you looked at the
linter, not that you handled the rejection.

Exception: fire-and-forget telemetry, which still gets a `.catch()` — a swallowed
rejection is a choice, and choices are written down.

_Source: Power of 10 §7; `no-floating-promises: "error"` in ma-mf-confirmed._

## Parse at the boundary; trust the types inside it

```ts
const user = await res.json() as User            // no — a cast is a wish, not a check
const user = UserSchema.parse(await res.json())  // yes

function retry(times: number) { … }              // no — -1 and NaN both type-check
function retry(times: number) {
  if (!Number.isInteger(times) || times < 0) {
    throw new RangeError(`retry times must be a non-negative integer, got ${times}`)
  }
  …                                              // yes
}
```

TypeScript checks what you wrote, not what arrives. Every API response, env var, URL
param, `postMessage` payload and file read enters as `unknown` wearing a type you
asserted. `as` does not verify — it instructs the compiler to stop asking. The failure
lands far from the boundary, in code that had every right to trust its inputs.

Validate once, where data enters. Past that line, the types are real and code stops
defending itself — that is the payoff, and it is why the line has to be a line.

Exception: internal calls already behind a validated boundary. Re-checking there is
noise that trains readers to skim the checks that matter.

_Source: Power of 10 §5 and §7 (callee validates its parameters)._

## Strict from the first commit; a suppression carries its reason

```ts
// @ts-expect-error                              // no — reason-free
// eslint-disable-next-line                      // no

// @ts-expect-error — upstream types omit the `cause` field, fixed in v5 (#4412)
…                                                // yes
```

The rule is not "never suppress" — it is that a suppression is a claim, and a claim
needs a reason a later reader can check and eventually delete. A reason-free suppression
is indistinguishable from a mistake, so nobody ever removes it, and it outlives the
problem by years.

New code compiles clean under the repo's strictest available setting from its first
commit. Warnings tolerated on day one are warnings nobody reads on day one hundred —
the signal is gone long before the code is.

Do not loosen `tsconfig` to make a change compile. That trades a local problem for a
global one, and the trade is invisible in the diff.

_Source: Power of 10 §10; `strict: true` in openclaude's tsconfig._

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

A log-only catch is worse than no catch: it converts a failure into wrong behaviour that
keeps running, and it does so at exactly the point where the program still had enough
context to say something useful. Catch to _handle_ — recover, or rethrow with more
context than you were given.

Throw `Error` subclasses, never strings or object literals: only a real `Error` carries a
stack. Pass `{ cause }` when rethrowing — the original failure is the part worth keeping,
and a wrapper that discards it makes the new message the only clue.

Exception: a cleanup path in a `finally`, where a secondary failure must not mask the
original. Say so in a comment; that is the case this rule expects you to reason about.

_Source: openclaude — 254 catches typed `unknown`, `Error` hierarchy in `utils/errors.ts`._

## Return early; keep the happy path at the left margin

```ts
if (user) {
  // no
  if (user.active) {
    if (hasQuota(user)) {
      return grant(user);
    }
  }
}
return null;

if (!user) return null; // yes
if (!user.active) return null;
if (!hasQuota(user)) return null;
return grant(user);
```

Every level of indentation is a condition the reader has to hold in mind until the
closing brace. Nested happy paths spend that attention on bookkeeping, and the actual
work ends up furthest from the margin — hardest to find, hardest to change safely.

Guards also make the failure cases enumerable: three lines, three reasons, each one
readable and testable on its own.

Exception: none worth stating. If the guards outnumber the work, that is a signal the
function is doing two jobs, not that the rule is wrong.

_Source: Linux kernel, Go and Google style guides converge here._

## A function fits on one screen

A function you cannot see at once is a function nobody verifies — checking it means
scrolling while holding the first half in memory, so reviewers stop reading and start
trusting. That is where bugs live.

Length is a symptom. A very long function is almost never one idea that happens to be
long; it is several ideas that were never named. Extract the ideas and the length
resolves itself — splitting to hit a threshold produces fragments with no meaning, which
is worse than the long version. That is why this rule states no number.

Exception: a flat exhaustive `switch`, a config literal, a generated mapping — long
without being deep.

_Source: Power of 10 §4 (which does state one: ~60 lines)._

## Wait for the third occurrence before abstracting

Two similar blocks are a coincidence. Three is a pattern, and only the third one tells
you which parts actually vary — which is the entire question an abstraction has to answer
correctly to be worth having.

Abstracting at two guesses the axis of variation, and a wrong guess is expensive in a way
duplication is not. Duplicate code is honest: it is visibly repeated, and any reader can
see all of it. A wrong abstraction hides the repetition behind a shared function that
now needs a flag, then a second flag, then a branch that only one caller takes — and
unpicking it means understanding every call site at once.

```ts
function render(item, opts) {
  if (opts.isCard) …                   // no — flags accreting on a premature shared path
  if (opts.isRow && !opts.compact) …
}
```

A parameter that exists only to select behaviour is the signal that two things were
merged too early. Prefer inlining it back and waiting.

This binds hardest on generated code, which pattern-matches on shape and will happily
factor together two things that merely look alike.

Exception: a genuine contract you already know — an interface a third party defines, a
boundary the architecture requires. Those are designed, not discovered.

_Source: the rule of three (Fowler, ‹Refactoring›); reinforced by Google's readability
guidance on premature generalisation._

## Export by name, not by default

```ts
export default function parseManifest() { … }   // no
export function parseManifest() { … }           // yes

import parse from './manifest'                   // no — importer invents the name
import { parseManifest } from './manifest'       // yes
```

A default export has no name at its definition site, so every importer invents one.
Grep for the real name and you find the definition and none of the call sites. Rename
refactors stop working, because there is no shared symbol to rename. Two files end up
calling the same function `parse` and `loadManifest`, and neither is wrong.

This is also **Reuse the name a thing already has**, one level up: a default export forces a
rename at every boundary, which is the thing that rule exists to prevent.

Exception: frameworks that require it — a Next.js page or route, a config file the tool
loads by convention. Follow the framework; it is not a style choice there.

_Source: Google TypeScript Style Guide (default exports prohibited); openclaude — 4702
named exports to 138 default._

## Comments explain why, not what

```ts
// increment the counter
count++; // no — the code already said this

// Retry once on 429 before surfacing: the ranking API rate-limits per region and the
// second attempt almost always lands in a different bucket.
if (res.status === 429) return retryOnce(req); // yes
```

The compiler already documents _what_. A comment earns its place by carrying what the
code cannot: the constraint that forced this shape, the bug that made the obvious
version wrong, the reason a check that looks redundant is load-bearing.

The highest-value comment in any codebase usually explains a defeat. openclaude guards
against abort errors with an `instanceof` check rather than the obvious name comparison,
and the comment says why: minified builds mangle class names, so string matching passes
in dev and silently fails in production. Nobody would keep that check without the
comment — and deleting it would reintroduce a bug that only appears after a build step.

Write the comment for whoever arrives after the context is gone. That is usually you.

Exception: docblocks on a public API, where describing what it does _is_ the job.

_Source: Google, Apple and kernel style guides converge here; specimen from openclaude
`utils/errors.ts`._

## The change includes the deletion

```ts
export function formatPrice(v: number) { … }                  // old, still exported
export function formatPriceV2(v: number, c: Currency) { … }   // no — both are live now
```

Replacing something means removing what it replaced. The commented-out block, the export
with no remaining importer, the flag branch that can no longer be reached, the helper
whose last caller went away in this same diff — all of it ships in the change that made
it dead, not in a cleanup nobody schedules.

Version control already remembers. Commented-out code is not a backup, it is a question
the next reader cannot answer: was this disabled on purpose, is it about to come back,
is it safe to delete? Nobody can tell, so nobody touches it, and it stays for years.

This rule binds hardest on generated code, which adds far more readily than it removes.
A diff that only grows is worth a second look before it lands.

Exception: a deliberate deprecation window — which carries a dated removal note and a
replacement, not silence.

_Source: convergent across large-codebase review practice (Google, Meta); the failure is
amplified by generated code._

## A new dependency is a liability you are choosing

```ts
import { format } from "date-fns";
format(d, "dd/MM/yyyy"); // ~20kB shipped to render one date

new Intl.DateTimeFormat(locale).format(d); // yes — platform, zero bytes, localised
```

A dependency is never just its API. It is a supply-chain surface, a permanent upgrade
obligation, a bet on somebody else's maintenance, and — on the client — bytes on the
critical path, which is the entire budget that site-speed work is fighting for.

Before adding one, answer three questions in the PR: what does it cost to ship, what
happens when it stops being maintained, and how much of its surface do you actually use?
"One function" is usually the honest answer, and usually the argument against.

Reach for the platform first. `Intl`, `URL`, `URLSearchParams`, `structuredClone`,
`AbortSignal.timeout`, `Array.prototype.at` and `crypto.randomUUID` between them retire a
surprising number of packages, and they never need upgrading.

Exception: cryptography, time zones, and anything with a specification longer than this
file. Do not hand-roll those — the liability runs the other way.

_Source: convergent across Google, Apple and Meta dependency review; sharpened by the
site-speed work these skills do._

## Separate the decision from the action

```ts
async function cancel(id: string) {          // no — one function, untestable without I/O
  const sub = await db.load(id)
  if (sub.endsAt < new Date()) return
  if (sub.plan === 'trial') { await db.delete(id); await email.send(…); return }
  await db.update(id, { cancelled: true })
  await email.send(…)
}

function decideCancellation(sub: Sub, now: Date): CancelAction { … }  // yes — pure

async function cancel(id: string) {                                   // yes — thin shell
  const action = decideCancellation(await db.load(id), new Date())
  await apply(action)
}
```

Logic tangled with I/O can only be exercised through that I/O: asserting one branch needs
a database, a clock and a mail server. So the branch does not get tested — and the
branches that go untested are exactly the interesting ones, the expiry edge case, the
ordering, the "what if it was already cancelled".

Pulled out, the decision is a function of its arguments. No setup, no mocks, no waiting.
Passing `now` in rather than calling `new Date()` inside is part of the same move: a
function that reads the clock has a hidden input, and hidden inputs cannot be varied by a
test. What remains in the shell is thin enough to be checked by reading it.

Exception: code that is genuinely all action — a migration, a thin adapter. There is no
decision to extract, and inventing one adds a layer without adding a test.

_Source: Gary Bernhardt, "Boundaries" (2012) — functional core, imperative shell.
Surfaced by ‹7 Coding Laws of Senior Developer› (law 5)._

---

## What deliberately is not here

Owned by a skill, and restating it here would create two sources of truth:

| Topic                                              | Owner                          |
| -------------------------------------------------- | ------------------------------ |
| Test structure, what to assert, runner conventions | `write-tests`                  |
| Commit message shape, what may be staged           | `git-commit`                   |
| Branch naming                                      | `git-create-branch`            |
| Whether a change should exist at all               | `plan-change`, `critique-plan` |

Considered and rejected, so they are not re-proposed each time: **declare at narrowest
scope** (Power of 10 §6 — already the default for `const` in block scope, and the linter
covers the rest), **formatting is not a decision** (Prettier enforces it as an error; a
rule that only restates a config file teaches readers this file is skimmable),
**thread a cancellation signal** (real — openclaude threads `AbortSignal` through 422 call
sites — but narrower than the rules above; promote it if a run gets bitten), and
**make invalid states unrepresentable** (Minsky, 2011 — proposed from ‹7 Coding Laws of
Senior Developer› law 4, and declined).

Power of 10 §1 (no recursion), §3 (no dynamic allocation after init), §8 (preprocessor
limits) and §9 (one level of pointer dereference, no function pointers) have no honest
analogue in TypeScript and were dropped rather than forced into one.
