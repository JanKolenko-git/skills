# Engineering rules

## Answer from the official source, read now

A question about a platform, library or service is answered from its official documentation,
read now, not from memory. Other trusted sources come after, and the answer says which was
read. Except: the official page is silent or wrong on the point; say so and cite what you
used.

## Simple code beats a marginal improvement

Put a number on what each part of a change buys before building it; small next to its lines
means drop it. A part that needs propping constants and comments, complicates shared code, or
grows a special case per fix round is not earning its lines: find the angle where simple code
keeps working, or take the part and its number to the user. Except: the simple code was wrong
for every caller; fix it as its own change.

## Reuse the name a thing already has; give a new one meaning

A renamed alias loses its documentation and a default export leaves every importer to invent
a name, so grep finds the definition and none of its uses. Name what you invent by its
meaning, not its shape: `order`, not `data`. Except: a collision, a framework that requires a
default export, generic code where an item really is any item.

## Derived artifacts are regenerated with the pinned toolchain, in the commit that changed their source

An artifact that disagrees with its source lies to every reader, and a generator on an
unpinned version emits output that passes tests and is wrong in bulk. Match the pin and learn
what the package regenerates before calling a change verified. Except: artifacts the repo
does not commit; one you cannot regenerate is called stale, never committed silently.

## Parse at the boundary; trust the types inside it

Everything that enters from outside arrives as `unknown` wearing a type you asserted, and a
cast is a wish, not a check. Validate once where data enters, a library's public props
included, and warn on an unrecognised value instead of falling through in silence. Except:
internal calls already behind a validated boundary.

## Comments say why, in two sentences at most, and are checked like code

The compiler documents what and a name documents a value; a comment carries only the
constraint, bug or load-bearing check that neither can, said once where it lives, and one
that wants a paragraph stands in for a name the code lacks. When a mechanism moves, grep for
its old story; a comment that says a case is handled points at the line that does. Except: a
docblock on a published surface may say what, in two sentences; a comment about the world
outside the code is dated or cited.

## An edit is verified by reading it back, not by the tool that applied it

A tool that applies an edit reports its own success and can succeed while changing nothing;
the diff is the fact about the code, so read it for every file touched, hardest where nothing
else will look: a test the session cannot run, a config no build loads. Except: an edit
followed by a check that exercises it; the check is the read-back.

## Every loop, retry and poll carries a bound

An unbounded loop fails by hanging, with no stack trace and no log line; a bound turns that
into a failure with a message. Name the constant, and give a network call a timeout. Except:
a genuine event loop or long-lived consumer, whose shutdown path is then explicit.

## Every result is checked; every promise is awaited or handled

A floating promise surfaces in another tick with no stack pointing at its cause, and an
unchecked response status turns a 500 into a type error three layers away. `void` silences
the linter, not the bug; a `.catch()` is handling. Except: fire-and-forget telemetry, which
still gets a `.catch()`.

## Strict from the first commit; a suppression carries its reason

A reason-free suppression is indistinguishable from a mistake and outlives the problem by
years. New code compiles clean under the repo's strictest setting; never loosen the compiler
config to make a change compile.

## Errors are typed, narrowed and never swallowed

A log-only catch turns a failure into wrong behaviour that keeps running, at the one point
with enough context to say something useful. Narrow the error, recover, or rethrow an `Error`
subclass with `{ cause }`; never throw a string, which carries no stack. Except: a cleanup
path in `finally`, where a secondary failure must not mask the original; say so in a comment.

## Return early; keep the happy path at the left margin

Every level of indentation is a condition the reader holds until the closing brace; guards
make the failure cases enumerable and put the work at the margin. Guards outnumbering the
work means the function does two jobs.

## A function fits on one screen

A function you cannot see at once is one nobody verifies: reviewers scroll, then trust.
Extract the ideas the length hides rather than split at a line count, which is why this rule
states no number. Except: a flat exhaustive `switch`, a config literal, a generated mapping.

## Wait for the third occurrence before abstracting

Two similar blocks are a coincidence; the third shows which parts vary, which is what an
abstraction has to answer, and one made at two grows a flag per caller: a parameter that only
selects behaviour is the tell. Generated code pattern-matches on shape, so this binds hardest
there. Except: a contract you already know, from a third party or the architecture.

## The change includes the deletion

Replacing something means removing what it replaced in the same diff, down to the helper
whose last caller just left; version control remembers. A deletion is proven where the thing
is used at runtime, not where it is imported: a stylesheet is dead only when the rendered
DOM, in every state, uses none of its classes. Except: a deliberate deprecation window, with
a dated removal note and a replacement.

## A new dependency is a liability you are choosing

A dependency is a supply-chain surface, an upgrade obligation and, on the client, bytes on
the critical path. Before adding one, say in the PR what it costs to ship, what happens when
it goes unmaintained and how much of it you use; reach for the platform first. Except:
cryptography, time zones, and anything with a specification longer than this file.

## Separate the decision from the action

Logic tangled with I/O can only be tested through that I/O, so the interesting branches go
untested. Pull the decision out as a pure function of its arguments, the current time
included, since a function that reads the clock has a hidden input no test can vary. Except:
code that is genuinely all action, a migration or a thin adapter.
